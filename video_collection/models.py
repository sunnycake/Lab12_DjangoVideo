from urllib import parse
from django.db import models
from django.core.exceptions import ValidationError

class Video(models.Model):
    name = models.CharField(max_length=200)
    url = models.CharField(max_length=400)
    notes = models.TextField(blank=True, null=True)
    video_id = models.CharField(max_length=40, unique=True)

    def save(self, *args, **kwargs):
        # # Check if url is a valid youtube.com... url
        # if not self.url.startswith('https://www.youtube.com/watch'):
        #     raise ValidationError(f'Not a YouTube URL {self.url}')

        # extract video id from youtube url
        url_components = parse.urlparse(self.url)

        if url_components.scheme != 'https':
            raise ValidationError(f'Not a YouTube URL {self.url}')

        if url_components.netloc != 'www.youtube.com':
            raise ValidationError(f'Not a YouTube URL {self.url}')
            
        if url_components.path != '/watch':
            raise ValidationError(f'Not a YouTube URL {self.url}')

        query_string = url_components.query # v = "1234567"
        if not query_string: # If no query string, raise validation error
            raise ValidationError(f'Invalid YouTube URL {self.url}')
        # Get query parameters
        parameters = parse.parse_qs(query_string, strict_parsing=True) # dictionary   
        v_parameter_list = parameters.get('v') # get v key, return None if no key found.
        if not v_parameter_list:   # If v parameter exists, this will be true if not None
            raise ValidationError(f'Invalid YouTube URL, missing parameters {self.url}')
        # If neither of the above raise a validation error
        self.video_id = v_parameter_list[0]

        super().save(*args, **kwargs)

    def __str__(self):
        return f'ID: {self.pk}, Name: {self.name}, URL: {self.url}, Video ID: {self.video_id}, Notes: {self.notes[:200]}'