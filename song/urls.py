from django.urls import path
from . import views

urlpatterns = [
    # トップ画面
	path('', views.index, name='index'),
    path('top', views.reset_column_list, name='reset_column_list'),

    # サンプル画面
	path('sample', views.sample, name='sample'),

    # 結果画面
    #path('result/emotion/<str:emotion>/', views.sort_by_emotion, name='sort_by_emotion'),

    #path('result/feature/<str:feature>/', views.sort_by_feature, name='sort_by_feature'),

    path('result/<str:column>/', views.sort_songs, name='sort_songs'),
    
    # 2回目のソート結果を表示するページ
    #path('sort_and_display_songs_second/<str:emotion>/', views.sort_and_display_songs_second, name='sort_and_display_songs_second'),

    # Spotifyのプレイリストをデータベースに登録
    path('import_playlist_data/', views.import_playlist_data, name='import_playlist_data'),

    # 楽曲の歌詞データをデータベースに登録
    path('import_lyrics_data/', views.import_lyrics_data, name='import_lyrics_data'),

    # 感情分析結果をデータベースに登録
    path('import_song_score/', views.import_song_score, name='import_song_score'),
    
]