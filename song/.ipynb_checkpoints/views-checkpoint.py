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

def sample(request):
    return render(request, 'song/sample.html')

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
    playlist_uri = '32ou4DVYMMP8Zxm92qDuCT'  # プレイリストのSpotify URIに置き換えてください

    ids = get_track_ids(user, playlist_uri)
    tracks = []

    for i in range(len(ids)):
        time.sleep(.5)
        track = get_track_features(ids[i])
        tracks.append(track)

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
    
    # 最後に余分なカンマを削除
    lyric = lyric.strip('、')
    
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
        # 歌詞データを取得
        lyrics = get_lyric(title, artist)
        lyrics = fix_lyrics(lyrics)

        # 修正後の歌詞の長さが短い場合
        if len(lyrics) < 50:
            print(f"{title} - {artist} の歌詞が短すぎます")
            delete_songs(title, artist)

        if is_japanese(lyrics):
            # 歌詞が日本語の場合
            save_songs(title, artist, lyrics)
        else:
            # 歌詞が日本語でない場合
            print(f"{title} - {artist} の歌詞を表示できません")
            delete_songs(title, artist)

    return HttpResponse("楽曲の歌詞データをデータベースに登録しました.")

checkpoint = 'cl-tohoku/bert-base-japanese-whole-word-masking'
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForSequenceClassification.from_pretrained(f"/bert-sentiment-analysis")
def np_softmax(x):
    f_x = np.exp(x) / np.sum(np.exp(x))
    return f_x

def analyze_emotion2(text):
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

def import_songs(request):
    # 提供された曲のデータ
    lst3 = [('W / X / Y', 0.045452952, 0.31710723, 0.36596358, 0.011537299, 0.012008912, 0.11394371, 0.123284295, 0.010701977), 
            ('シンデレラボーイ', 0.011693709, 0.11641515, 0.012055786, 0.033770505, 0.1529066, 0.082226, 0.58603024, 0.00490204), 
            ('ベテルギウス', 0.55156165, 0.026170805, 0.16805212, 0.05478361, 0.0070301243, 0.037449133, 0.037702113, 0.11725043), 
            ('なんでもないよ、', 0.17844704, 0.11563788, 0.09111454, 0.07109496, 0.037118334, 0.07864865, 0.3797519, 0.048186712), 
            ('ドライフラワー', 0.022917915, 0.25682715, 0.034678526, 0.019896112, 0.029308064, 0.13824831, 0.49112615, 0.006997682), 
            ('水平線', 0.05215141, 0.16613379, 0.39204744, 0.034267996, 0.010818408, 0.21599044, 0.11219828, 0.01639233), 
            ('残響散歌', 0.092926964, 0.1634634, 0.39596918, 0.043319322, 0.016316226, 0.15706332, 0.10756276, 0.023378903), 
            ('シャッター', 0.16341391, 0.37783068, 0.052330244, 0.044705898, 0.013818053, 0.0914434, 0.23047142, 0.025986467), 
            ('ミックスナッツ', 0.10666902, 0.1275432, 0.15670206, 0.080809325, 0.014006214, 0.3527625, 0.1349934, 0.02651427), 
            ('CITRUS', 0.23168355, 0.038760506, 0.5608398, 0.02439161, 0.0072407033, 0.035433833, 0.04371425, 0.05793581), 
            ('逆夢', 0.10446193, 0.08078074, 0.59839493, 0.029259786, 0.0066109938, 0.10478735, 0.049999826, 0.025704462), 
            ('群青', 0.15476806, 0.13318512, 0.35214004, 0.035941068, 0.010776749, 0.18560933, 0.09743708, 0.030142536), 
            ('一途', 0.055682644, 0.26285005, 0.16053925, 0.027100073, 0.028799232, 0.15012032, 0.29867554, 0.016232915), 
            ('カメレオン', 0.019221859, 0.58253604, 0.034778517, 0.032346345, 0.0074339965, 0.18856849, 0.13103345, 0.0040813815), 
            ('点描の唄', 0.051166378, 0.31912032, 0.2764059, 0.016241342, 0.013828888, 0.14895032, 0.16030903, 0.0139778545), 
            ('Mela!', 0.019002253, 0.15525006, 0.26398504, 0.027103785, 0.0396846, 0.20353323, 0.2809413, 0.010499768), 
            ('夜に駆ける', 0.18223673, 0.12959489, 0.044145357, 0.11519747, 0.008238092, 0.39375103, 0.10566395, 0.021172516), 
            ('勿忘', 0.045438033, 0.17068881, 0.6352971, 0.012228433, 0.005852386, 0.0802473, 0.04069128, 0.009556663), 
            ('魔法の絨毯', 0.156518, 0.034449045, 0.7340297, 0.0073128087, 0.0041536735, 0.020020856, 0.019137213, 0.024378628), 
            ('Habit', 0.013368035, 0.1589955, 0.032053303, 0.01785228, 0.077798605, 0.12045656, 0.57397336, 0.0055023883), 
            ('常緑', 0.12572375, 0.094078496, 0.4997696, 0.035647947, 0.01691915, 0.07744347, 0.10976587, 0.04065174), 
            ('115万キロのフィルム', 0.07092207, 0.012925976, 0.86835206, 0.0077378857, 0.0029373118, 0.0111329695, 0.0102927005, 0.015699057), 
            ('Cry Baby', 0.057969883, 0.25628042, 0.05762247, 0.030624066, 0.027184997, 0.158638, 0.39843014, 0.01324999), 
            ('ダンスホール', 0.123914525, 0.0276937, 0.7729824, 0.010612241, 0.0028316383, 0.02439318, 0.013234063, 0.024338217), 
            ('ハート', 0.046485975, 0.1766191, 0.47271022, 0.014942026, 0.017096058, 0.110433884, 0.14588898, 0.01582374), 
            ('踊り子', 0.02835864, 0.12772815, 0.29494244, 0.026054244, 0.046277285, 0.22621731, 0.23656529, 0.013856563), 
            ('怪物', 0.050112106, 0.06734864, 0.69823843, 0.014225261, 0.014842909, 0.056153156, 0.07831371, 0.02076586), 
            ('愛とか恋とか', 0.16020082, 0.020391054, 0.76038325, 0.0062969616, 0.0022449878, 0.014162363, 0.009860957, 0.026459515), 
            ('Bye-Good-Bye', 0.056364972, 0.39102224, 0.27229473, 0.01680701, 0.011709147, 0.11710609, 0.122008964, 0.012686818), 
            ('三原色', 0.20643725, 0.046517022, 0.6321084, 0.020537807, 0.0036216173, 0.03883514, 0.023148524, 0.028794236), 
            ('Pretender', 0.1278, 0.20317523, 0.21492255, 0.04228981, 0.019155104, 0.13730559, 0.22366235, 0.0316893), 
            ('Stand by me, Stand by you.', 0.09316923, 0.27952266, 0.38695893, 0.028633527, 0.010753483, 0.095309556, 0.090086356, 0.0155662615), 
            ('ヨワネハキ', 0.030826453, 0.16592358, 0.16289502, 0.02825179, 0.0175408, 0.3772094, 0.2088032, 0.008549738), 
            ('恋風邪にのせて', 0.32510477, 0.09068487, 0.062353127, 0.25340497, 0.011483193, 0.100172564, 0.11399305, 0.042803474), 
            ('怪獣の花唄', 0.07212269, 0.30529955, 0.27057633, 0.031736273, 0.016715147, 0.13438433, 0.15087153, 0.018294163), 
            ('I LOVE...', 0.33162722, 0.11195537, 0.25662234, 0.05733795, 0.0110051185, 0.0974093, 0.08531918, 0.048723616), 
            ('いつか', 0.09294867, 0.41935232, 0.15740122, 0.040697817, 0.0078120874, 0.16388036, 0.10458141, 0.013326118), 
            ('KICK BACK', 0.07578016, 0.031406954, 0.83881396, 0.0060726325, 0.0034325444, 0.0144929215, 0.013964352, 0.01603658), 
            ('BOY', 0.36138272, 0.024828512, 0.50991035, 0.015526071, 0.0034051014, 0.021151815, 0.016860602, 0.04693486), 
            ('Subtitle', 0.019085426, 0.38228914, 0.13156898, 0.019976033, 0.021736244, 0.19338894, 0.22538179, 0.0065734163), 
            ('エジソン', 0.07561488, 0.023302, 0.6046498, 0.07912162, 0.040723026, 0.036387898, 0.11248909, 0.027711773), 
            ('もう少しだけ', 0.5324718, 0.0062540043, 0.36460993, 0.02014659, 0.0019890144, 0.0078902785, 0.004741867, 0.06189655), 
            ('虹', 0.44828665, 0.024940128, 0.4239698, 0.015055435, 0.0029287953, 0.018284576, 0.012959111, 0.053575456), 
            ('Overdose', 0.009173277, 0.3268943, 0.029462144, 0.01665756, 0.032551166, 0.15977243, 0.42160255, 0.0038865628), 
            ('スパークル', 0.12350184, 0.2523642, 0.06787244, 0.070964515, 0.012289639, 0.25802323, 0.19631357, 0.018670592), 
            ('怪盗', 0.028973006, 0.08775854, 0.21617109, 0.05853498, 0.10773766, 0.17629957, 0.30974174, 0.01478338), 
            ('のびしろ', 0.092177734, 0.13544616, 0.13270201, 0.05510845, 0.05408797, 0.10601259, 0.3957739, 0.028691158), 
            ('napori', 0.06536492, 0.18016359, 0.2564774, 0.04458153, 0.022412641, 0.21210276, 0.20130615, 0.01759109), 
            ('恋だろ', 0.37586364, 0.060770553, 0.33368233, 0.033824217, 0.009306674, 0.04746556, 0.07227588, 0.066811144), 
            ('結', 0.029727334, 0.23927395, 0.40898353, 0.013489203, 0.01301091, 0.18158415, 0.10617537, 0.007755537), 
            ('花占い', 0.16385901, 0.049831618, 0.67007345, 0.02010174, 0.003980877, 0.036045607, 0.027607497, 0.028500216), 
            ('青と夏', 0.14111745, 0.17635205, 0.37984303, 0.03342472, 0.013654456, 0.1119267, 0.11490159, 0.02878), 
            ('レオ', 0.3231215, 0.08953817, 0.05756843, 0.09768701, 0.0062280633, 0.31625044, 0.077105395, 0.032501012), 
            ('ミライチズ', 0.5207855, 0.008913913, 0.35382414, 0.014912068, 0.0038972276, 0.0074873245, 0.010007424, 0.08017237), 
            ('雨燦々', 0.04509113, 0.22583899, 0.36364254, 0.02288234, 0.011581324, 0.20662028, 0.11222283, 0.012120652), 
            ('死ぬのがいいわ', 0.0341213, 0.113494955, 0.07870798, 0.03206349, 0.0740359, 0.13509741, 0.51890767, 0.01357134), 
            ('ツキミソウ', 0.012218088, 0.30197933, 0.05426906, 0.022339683, 0.033110373, 0.21229665, 0.35857898, 0.0052078823), 
            ('かくれんぼ', 0.0102504315, 0.06808675, 0.01213769, 0.037463106, 0.20361583, 0.058482558, 0.60463184, 0.005331818), 
            ('白日', 0.01989511, 0.2134183, 0.1964075, 0.023575246, 0.03789868, 0.21775037, 0.2816404, 0.009414378), 
            ('ブルーベリー・ナイツ', 0.018225547, 0.17688753, 0.03803958, 0.012070091, 0.055867504, 0.07951811, 0.61184824, 0.007543486), 
            ('チェリー', 0.1973318, 0.04725277, 0.67104316, 0.011942145, 0.002748373, 0.030200131, 0.015067216, 0.024414347), 
            ('君に夢中', 0.0292767, 0.18190336, 0.11437788, 0.022953512, 0.042033736, 0.1546826, 0.4432965, 0.011475672), 
            ('不可幸力', 0.03589558, 0.26458114, 0.049054734, 0.026751203, 0.021304047, 0.15098481, 0.4382112, 0.01321725), 
            ('Bluma to Lunch', 0.069263816, 0.053767268, 0.7189318, 0.021720573, 0.010936599, 0.044332087, 0.06163982, 0.01940799), 
            ('マリーゴールド', 0.50015163, 0.048666537, 0.3035222, 0.026753962, 0.0039439104, 0.032664683, 0.029003577, 0.055293452), 
            ('魔法にかけられて', 0.091445364, 0.13501465, 0.07633635, 0.050618026, 0.045983747, 0.12603933, 0.44368026, 0.030882325), 
            ('裸の心', 0.6466744, 0.027823245, 0.19897726, 0.027115157, 0.002524351, 0.023056269, 0.017938904, 0.05589038), 
            ('阿修羅ちゃん', 0.049726915, 0.07808271, 0.1222322, 0.048336253, 0.13064, 0.087754525, 0.46576652, 0.017460866)]

    # データベースに曲のデータを登録
    for song_data in lst3:
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
            existing_song.snrai = sinrai
            existing_song.save()
        else:
            # 曲の名前がデータベースに存在しない場合は新たに登録
            new_song = Song(name=name, yorokobi=yorokobi, kanasimi=kanasimi, kitai=kitai, odoroki=odoroki, ikari=ikari, osore=osore, keno=keno, sinrai=sinrai)
            new_song.save()

    return HttpResponse("曲データをデータベースに登録しました。")

def sort_by_emotion(request, emotion):
    # ボタンから送られた感情（'yorokobi', 'kanasimi', 'kitai', 'odoroki', 'ikari', 'osore', 'keno', 'sinrai'）を受け取る

    if emotion not in ['yorokobi', 'kanasimi', 'kitai', 'odoroki', 'ikari', 'osore', 'keno', 'sinrai']:
        return HttpResponse("無効な感情が指定されました。")

    # 感情に応じて降順にソート
    songs = Song.objects.order_by('-{}'.format(emotion))

    # 上位50％の楽曲を計算
    total_songs = songs.count()
    display_count = int(total_songs * 0.5)

    # 上位80％を抽出
    top_songs = songs[:display_count]

    # セッションに最初の感情情報を保存
    request.session['first_emotion'] = emotion

    context = {
        'emotion': emotion,
        'top_songs': top_songs
    }

    return render(request, 'song/result.html', context)

def sort_by_feature(request, feature):
    
    if feature not in ['release_date', 'length', 'popularity', 'danceability', 'acousticness', 
                       'energy', 'instrumentalness', 'liveness', 'loudness', 'tempo']:
        return HttpResponse("無効な特徴が指定されました。")

    # 特徴に応じて降順にソート
    songs = Song.objects.order_by('-{}'.format(feature))

    # 上位50％の楽曲を計算
    total_songs = songs.count()
    display_count = int(total_songs * 0.5)

    # 上位50％を抽出
    top_songs = songs[:display_count]

    # セッションに最初の感情情報を保存
    request.session['first_feature'] = feature

    context = {
        'feature': feature,
        'top_songs': top_songs
    }

    return render(request, 'song/result.html', context)

def sort_and_display_songs_second(request, emotion):
    if emotion not in ['yorokobi', 'kanasimi', 'kitai', 'odoroki', 'ikari', 'osore', 'keno', 'sinrai']:
        return HttpResponse("無効な感情が指定されました。")

    # 最初の感情に応じてソートされた楽曲を取得
    first_emotion = request.session.get('first_emotion', None)
    if first_emotion:
        songs = Song.objects.order_by('-{}'.format(first_emotion))
        total_songs = songs.count()
        display_count = int(total_songs * 0.5)
        top_songs = songs[:display_count]
    else:
        return HttpResponse("最初の感情が指定されていません。")

    # 2回目の感情に応じてソート
    sorted_songs = sorted(top_songs, key=lambda song: getattr(song, emotion), reverse=True)
    total_songs = len(sorted_songs)
    display_count = int(total_songs * 0.5)
    top_songs = sorted_songs[:display_count]

    context = {
        'first_emotion': first_emotion,
        'emotion': emotion,
        'sorted_songs': top_songs
    }

    return render(request, 'song/result_second.html', context)

"""
def sort_and_display_songs(request, emotion):
    # ボタンから送られた感情（'yorokobi', 'kanasimi', 'kitai', 'odoroki', 'ikari', 'osore', 'keno', 'sinrai'）を受け取る

    if emotion not in ['yorokobi', 'kanasimi', 'kitai', 'odoroki', 'ikari', 'osore', 'keno', 'sinrai']:
        return HttpResponse("無効な感情が指定されました。")

    # 最初のソートかどうかをfirst_emotionがあるかないかで判定
    if 'first_emotion' not in request.session:
        request.session['first_emotion'] = emotion
        songs = Song.objects.order_by('-{}'.format(emotion))

        # 上位80％の楽曲を計算
        total_songs = songs.count()
        display_count = int(total_songs * 0.8)

        # 上位80％を抽出
        top_songs = songs[:display_count]

        # resultとしてtop_songsの内容を保存
        request.session['result'] = list(top_songs)

        context = {
            'first_emotion': emotion,
            'emotion': emotion,
            'top_songs': top_songs
        }

    # 二回目以降のソート ここの処理を繰り返す
    else:
        first_emotion = request.session['first_emotion']
        result = request.session.get('result', [])
        
        # 感情に応じて降順にソート
        result.sort(key=lambda song: getattr(song, emotion), reverse=True)
        
        # 上位80％の楽曲を計算
        total_songs = len(result)
        display_count = int(total_songs * 0.8)
        
        # 上位80％を抽出
        top_songs = result[:display_count]

        # セッションに前回の感情情報を保存
        request.session['first_emotion'] = emotion

        # resultに抽出した結果を保存
        request.session['result'] = list(top_songs)

        context = {
            'first_emotion': first_emotion,
            'emotion': emotion,
            'top_songs': top_songs,
            'result': result
        }

    return render(request, 'song/result.html', context)

"""

