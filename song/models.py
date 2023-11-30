from django.db import models

# Create your models here.
class Song(models.Model):
    name = models.TextField(max_length=200)
    artist = models.TextField(max_length=200)
    release_date = models.TextField(max_length=200)
    length = models.IntegerField()
    popularity = models.IntegerField()
    img_url = models.TextField(default='', max_length=200)
    prev_url = models.TextField(null=True, max_length=200)
    danceability = models.FloatField()
    acousticness = models.FloatField()
    energy = models.FloatField()
    instrumentalness = models.FloatField() 
    liveness = models.FloatField()
    loudness = models.FloatField()
    tempo = models.FloatField()
    track_uri = models.TextField(max_length=255)

    yorokobi = models.FloatField(default=0.0) 
    kanasimi = models.FloatField(default=0.0)
    kitai = models.FloatField(default=0.0)
    odoroki = models.FloatField(default=0.0)
    ikari = models.FloatField(default=0.0) 
    osore = models.FloatField(default=0.0)
    keno = models.FloatField(default=0.0)
    sinrai = models.FloatField(default=0.0)

    lyrics = models.TextField(default='', max_length=2000)

    @property
    def formatted_length(self):
        minutes = self.length // 60000
        seconds = (self.length % 60000) // 1000
        return f"{minutes}:{seconds:02d}"