from django.shortcuts import render
from django.http import HttpResponse
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from .models import Song 
import time
from lyricsgenius import Genius
from langdetect import detect
import re
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# Create your views here.
def index(request):
    return render(request, 'song/index.html')

# Spotify APIの認証情報を設定
def authenticate_spotify():
    client_id = '2e68aa39380d4fc1b84b3e4cfcd6610d'  # ご自身のSpotifyアプリのクライアントIDに置き換えてください
    client_secret = 'fdc83d9f91e641399b65490f3a737376'  # ご自身のSpotifyアプリのクライアントシークレットに置き換えてください
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    return sp

# プレイリストからトラックのIDを取得
def get_track_ids(user, playlist_id):
    sp = authenticate_spotify()
    ids = []
    playlist = sp.user_playlist(user, playlist_id)
    for item in playlist['tracks']['items']:
        track = item['track']
        if track != None:
            ids.append(track['id'])
    return ids

# トラックの特徴を取得
def get_track_features(id):
    sp = authenticate_spotify()
    meta = sp.track(id)
    features = sp.audio_features(id)

    name = meta['name']
    artist = meta['album']['artists'][0]['name']
    release_date = meta['album']['release_date']
    length = meta['duration_ms']
    popularity = meta['popularity']
    img_url = meta['album']['images'][0]['url']
    prev_url = meta['preview_url']

    acousticness = features[0]['acousticness']
    danceability = features[0]['danceability']
    energy = features[0]['energy']
    instrumentalness = features[0]['instrumentalness']
    liveness = features[0]['liveness']
    loudness = features[0]['loudness']
    tempo = features[0]['tempo']
    track_uri = features[0]['uri']

    track = [name, artist, release_date, length,
             popularity, img_url, prev_url, danceability, acousticness, energy,
             instrumentalness, liveness, loudness,
             tempo, track_uri]
    return track

# プレイリスト内のトラック情報をデータベースに登録
def import_playlist_data(request):
    # あらかじめ与えられたユーザー名とプレイリストのURL（URI）を設定
    user = 'paiiwkkwnqvwoazf0ru46t7i0'  # ご自身のSpotifyユーザー名に置き換えてください
    playlist_uri = '37i9dQZF1DX6UkADhBpEnE'  # プレイリストのSpotify URIに置き換えてください

    #'32ou4DVYMMP8Zxm92qDuCT':Top Tracks of 2022 in Japan(100)
    #'37i9dQZF1DXdcuhTbpro3s':100 Million+(87)
    #'37i9dQZEVXbKXQ4mDTEBXq':トップ50-日本(50)
    #'37i9dQZF1DXdbRLJPSmnyq':J-pop Hits(90)

    #'37i9dQZF1DWVVbqQrqciCF':This is YOASOBI(44)
    #'37i9dQZF1DX0MkpDFqXa80':This is Official髭男dism(65)
    #'37i9dQZF1DX8areMEHPwto':This is back number(49)
    #'37i9dQZF1DXdPcuTtZNPGI':This is Ado(53)
    #'37i9dQZF1DX5B7iHF4KS02':This is Mrs.GREEN APPLE(88) ERROR検出
    #'37i9dQZF1DZ06evO06GanS':This is 優里(17)
    #'37i9dQZF1DWYoL6ZoD9KnI':This is 米津玄師(67)
    #'37i9dQZF1DWZ7hCgzgU48z':This is あいみょん(65)
    #'37i9dQZF1DWXYQRh3xeYje':This is Vaundy(57) ERROR検出
    #'37i9dQZF1DX0f8F9n3N8ae':This is SEKAI NO OWARI(52)
    #'37i9dQZF1DXcmREjonh06P':This is Saucy Dog(48) ERROR検出
    #'37i9dQZF1DX0BqCYCcGsrh':This is RADWINPS(86)
    #'37i9dQZF1DZ06evO37Zxtr':This is ポルノグラフィテ(51)
    #'37i9dQZF1DX6PwVORlfZ4K':This is マカロニえんぴつ(76) ERROR検出
    #'37i9dQZF1DWYLp3LpUUY2V':This is ヨルシカ(66) ERROR検出
    #'37i9dQZF1DX9W0gpVB2iui':This is 菅田将暉(46) ERROR検出

    #'7hQ8uWEqha83PLzrkvUdWL':テスト 元気が出る曲(13)
    #'10mbNUX3nAv1yT2L4SdzSq':テスト 悲しい曲(14)
    #'37i9dQZF1DX6UkADhBpEnE':元気Booster(100)

    ids = get_track_ids(user, playlist_uri)
    tracks = []
    sp = authenticate_spotify()

    for i in range(len(ids)):
        time.sleep(.5)
        market = sp.track(ids[i])['available_markets']
        res = 'JP' in market
        if not (res == False and len(market) != 0):
            track = get_track_features(ids[i])
            tracks.append(track)
            print(f"登録しました")

    # データベースにトラック情報を登録
    for track_info in tracks:
        name, artist = track_info[0], track_info[1]
        if not Song.objects.filter(name=name, artist=artist).exists():
            song = Song(
                name=name,
                artist=artist,
                release_date=track_info[2],
                length=track_info[3],
                popularity=track_info[4],
                img_url=track_info[5],
                prev_url=track_info[6],
                danceability=track_info[7],
                acousticness=track_info[8],
                energy=track_info[9],
                instrumentalness=track_info[10],
                liveness=track_info[11],
                loudness=track_info[12],
                tempo=track_info[13],
                track_uri=track_info[14],
            )
            song.save()

    return HttpResponse("プレイリスト内の楽曲データをデータベースに登録しました。")

# データベースからタイトル名とアーティスト名を抽出
def extract_titles_and_artists():
    songs = Song.objects.all()  # Songモデルのすべてのレコードを取得

    # タイトル名とアーティスト名を格納するリストを初期化
    titles_and_artists = []

    for song in songs:
        title = song.name
        artist = song.artist
        titles_and_artists.append((title, artist))

    return titles_and_artists

# Genius APIのアクセストークンを設定
token = 'bXijqv5J-VyRtfF65mDNQ6-bMSeZhDhr9LD0T26oL3Os0TLOSEtb46jLMj30ACt0'
genius = Genius(token)

# Genius APIを使用して歌詞を検索
def get_lyric(title, artist):
    try:
        song = genius.search_song(title, artist)
        lyric = song.lyrics
        return lyric

    except AttributeError:
        print(f"{title} - {artist} の歌詞データがありません")
        return 'NO DATA'
        # データベースから削除するなどの処理をここに追加

#テキストが日本語かどうか判定する
def is_japanese(text):
    try:
        # テキストの言語を検出
        language = detect(text)
        # 日本語の言語コードは 'ja' です
        return language == 'ja'
    except:
        # 言語検出に失敗した場合、日本語でないとみなします
        return False
    
# 与えられたテキストデータから記号、数字、英語の文字を削除する関数
def fix_lyrics(lyric):
    # 歌詞の前についている数字と改行を削除
    lyric = re.sub(r'^[0-9].+\n\n', '', lyric)
    
    # 歌詞内の [ ] 内のテキストを削除
    lyric = re.sub(r'\[[^\]]*\]', '', lyric)
    
    # 英字、数字、記号を削除
    lyric = re.sub(r'[a-zA-Z!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~]+', '', lyric)
    
    # 連続した改行とスペースを単一のカンマに置換
    lyric = re.sub(r'[\n\s]+', '、', lyric)
    
    # 不要なユニコード空白文字を削除
    lyric = re.sub(r'[\u2000-\u200a\u205f\u200b]', '', lyric)
    
    # 数字と句点の組み合わせを削除
    lyric = re.sub(r'\d+、', '', lyric)
    
    # 連続した句点の組み合わせを削除
    lyric = re.sub(r'、+', '、', lyric)
    
    # 最後に余分なカンマを削除
    lyric = lyric.strip('、')
    
    # 末尾の句点と数字の組み合わせを削除
    lyric = re.sub(r'、\d+$', '', lyric)
    
    return lyric

# 楽曲データを削除する関数
def delete_songs(name, artist):
    try:
        song = Song.objects.get(name=name, artist=artist)
        song.delete()
        return f"{name} - {artist} のデータを削除しました"
    except Song.DoesNotExist:
        return f"{name} - {artist} のデータが見つかりません"
    except Exception as e:
        return f"エラー: {str(e)}"

# 歌詞をデータベースに登録する関数
def save_songs(title, artist, lyrics):
    try:
        song = Song.objects.get(name=title, artist=artist)
        song.lyrics = lyrics
        song.save()
        return f"{title} - {artist} の歌詞をデータベースに登録しました"
    except Song.DoesNotExist:
        return f"{title} - {artist} のデータがデータベースに存在しません"
    except Exception as e:
        return f"エラー: {str(e)}"

# 楽曲の歌詞データを取得する関数    
def import_lyrics_data(request):

    # タイトル名とアーティスト名を抽出
    titles_and_artists = extract_titles_and_artists()

    for title, artist in titles_and_artists:
        if Song.objects.filter(name=title, artist=artist, lyrics='').exists():
            # 歌詞データを取得
            lyrics = get_lyric(title, artist)
            lyrics = fix_lyrics(lyrics)
            
            # 修正後の歌詞の長さが短い場合
            if len(lyrics) < 50 or len(lyrics) > 2000:
                print(f"{title} - {artist} の歌詞の長さが適切ではありません")
                delete_songs(title, artist)
            elif is_japanese(lyrics):
                # 歌詞が日本語の場合
                print(f"{title} - {artist} の歌詞を登録しました")
                save_songs(title, artist, lyrics)
            else:
                # 歌詞が日本語でない場合
                print(f"{title} - {artist} の歌詞を表示できません")
                delete_songs(title, artist)

    return HttpResponse("楽曲の歌詞データをデータベースに登録しました")

from os.path import dirname
checkpoint = 'cl-tohoku/bert-base-japanese-whole-word-masking'
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForSequenceClassification.from_pretrained(f'{dirname(__file__)}/sentimentanalysis/')
def np_softmax(x):
    f_x = np.exp(x) / np.sum(np.exp(x))
    return f_x

def analyze_emotion(text):
    # 推論モードを有効か
    model.eval()

    emotion_names_jp = ['喜び', '悲しみ', '期待', '驚き', '怒り', '恐れ', '嫌悪', '信頼'] 

    # 入力データ変換 + 推論
    tokens = tokenizer(text, truncation=True, return_tensors="pt")
    tokens.to(model.device)
    preds = model(**tokens)
    prob = np_softmax(preds.logits.cpu().detach().numpy()[0])
    out_dict = {n: p for n, p in zip(emotion_names_jp, prob)}
    
    return out_dict

def import_song_score(request):
    #歌詞情報をデータベースから抽出
    songs = Song.objects.all()  # Songモデルのすべてのレコードを取得

    # タイトル名と歌詞を格納するリストを初期化
    titles_and_lyrics = []
    titles_and_scores = []

    for song in songs:
        title = song.name
        lyric = song.lyrics
        titles_and_lyrics.append((title, lyric))

    # 歌詞の感情分析
    if Song.objects.filter(name=title, lyrics=lyric, yorokobi=0.0).exists():
        for title, lyric in titles_and_lyrics:
            score = analyze_emotion(lyric)
            titles_and_scores.append((title,score['喜び'],score['悲しみ'],score['期待'],score['驚き'],score['怒り'],score['恐れ'],score['嫌悪'],score['信頼']))

        for song_data in titles_and_scores:
            name, yorokobi, kanasimi, kitai, odoroki, ikari, osore, keno, sinrai = song_data
            existing_song = Song.objects.filter(name=name).first()
            if existing_song is not None:
                # 曲の名前が既にデータベースに存在する場合は更新
                existing_song.yorokobi = yorokobi
                existing_song.kanasimi = kanasimi
                existing_song.kitai = kitai
                existing_song.odoroki = odoroki
                existing_song.ikari = ikari
                existing_song.osore = osore
                existing_song.keno = keno
                existing_song.sinrai = sinrai
                existing_song.save()
                print(f"登録しました")
            else:
                # 曲の名前がデータベースに存在しない場合は新たに登録
                new_song = Song(name=name, yorokobi=yorokobi, kanasimi=kanasimi, kitai=kitai, odoroki=odoroki, ikari=ikari, osore=osore, keno=keno, sinrai=sinrai)
                new_song.save()

    return HttpResponse("感情分析のスコアをデータベースに登録しました。")

def write_sql(column_list):
    for i in range(len(column_list)):
        column_name = column_list[i]
        if i == 0:
            display_number = 100
            sql = """SELECT *
FROM song_song
ORDER BY """ +column_name+ """ DESC
LIMIT """ +str(display_number)
        else:
            display_number *= 0.5
            if display_number >= 10:
                sql = """SELECT *
FROM
(""" +sql+ """) 
ORDER BY """ +column_name+ """ DESC
LIMIT """ +str(round(display_number))
            else:
                break
    return sql+';'

def sort_songs(request, column):
    column_list = request.session.get('column_list', [])
    column_list.append(column)  # columnを追加

    # 実際のSQL文に置き換える必要があります
    sql_query = write_sql(column_list)

    # SQL文を実行して結果を取得
    result = Song.objects.raw(sql_query)

    # セッションに情報を保存
    request.session['column_list'] = column_list

    context = {
        'column': column,
        'result': result
    }
    print(column_list,'\n')
    return render(request, 'song/result.html', context)

def reset_column_list(request):
    # セッションから'column_list'を削除
    if 'column_list' in request.session:
        del request.session['column_list']
    
    return render(request, 'song/index.html')

#サンプルコード
from django.db.models import F
def sample(request):
    return render(request, 'song/sample3.html')

def top_songs(request):
    # データベースから上位10件の曲を取得
    top_songs = Song.objects.order_by('-{}'.format('name'))[:5]
    return render(request, 'song/sample2.html', {'top_songs': top_songs})



