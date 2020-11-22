from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from .models import Video

class TestHomePageMessage(TestCase):

    def test_app_title_message_shown_on_home_page(self):
        url = reverse('home')
        response = self.client.get(url)
        # examine a [HTTP] response & see if it contains a particular piece of text
        self.assertContains(response, 'Vegan Recipes Videos')

class TestAddVideos(TestCase):

    def test_add_video(self):

        valid_video = {
            'name': 'vegan',
            'url': 'https://www.youtube.com/watch?v=U8_umxNW_A4',
            'notes': 'vegan Jjajangmyeon by Seonkyoung Longest'
        }

        url = reverse('add_video')
        # if redirected then follow that redirect. allow that next request to take place
        response = self.client.post(url, data=valid_video, follow=True)

        self.assertTemplateUsed('video_collection/video_list.html')

        # does the video list show the new video?
        self.assertContains(response, 'vegan')
        self.assertContains(response, 'vegan Jjajangmyeon by Seonkyoung Longest')
        self.assertContains(response, 'https://www.youtube.com/watch?v=U8_umxNW_A4')

        # check db to make sure the db was modified correctly
        video_count = Video.objects.count()
        self.assertEqual(1, video_count)

        # checking that all of this example data is being added. Check name, url, notes are all there
        video = Video.objects.first()

        # check to see if the, the attributes of this video are the same as the attributes of the data
        self.assertEqual('vegan', video.name)
        self.assertEqual('https://www.youtube.com/watch?v=U8_umxNW_A4', video.url)
        self.assertEqual('vegan Jjajangmyeon by Seonkyoung Longest', video.notes)
        self.assertEqual('U8_umxNW_A4', video.video_id)

    # test error condition. If duplicate video or added video with a URL that's not valid or not a YouTube URL
    def test_add_video_invalid_url_not_added(self):

        invalid_video_urls = [
            'https://www.youtube.com/watch',
            'https://www.youtube.com/watch?',
            'https://www.youtube.com/watch?abc=123',
            'https://www.youtube.com/watch?v=',
            'https://www.github.com',
            'https://minneapolis.edu',
            'https://minneapolis.edu?v=123456'

        ]

        for invalid_video_url in invalid_video_urls:

            new_video = {
                'name': 'example',
                'url': invalid_video_url,
                'notes': 'example notes'
            }

            url = reverse('add_video')
            response = self.client.post(url, new_video)

            self.assertTemplateUsed('video_collection/add.html')

            messages = response.context['messages']
            # for every message in the messages list, extract hat message's message then save to a new list
            message_texts = [ message.message for message in messages ]
            self.assertIn('Invalid YouTube URL', message_texts)
            self.assertIn('Please check the data entered.', message_texts)

            #  check to make sure there's no data in the database
            video_count = Video.objects.count()
            self.assertEqual(0, video_count)
            
# test video list. Are all of videos from the db displayed? Do they have all of the right data? 
# Are they ordered in name order but case insensitive?
class TestVideoList(TestCase):

    def test_all_videos_displayed_in_correct_order(self):

        v1 = Video.objects.create(name='XYZ', notes='example', url='https://www.youtube.com/watch?v=123')
        v2 = Video.objects.create(name='abc', notes='example', url='https://www.youtube.com/watch?v=124')
        v3 = Video.objects.create(name='AAA', notes='example', url='https://www.youtube.com/watch?v=125')
        v4 = Video.objects.create(name='lmn', notes='example', url='https://www.youtube.com/watch?v=126')

        expected_video_order = [ v3, v2, v4, v1 ]

        url = reverse('video_list')
        response = self.client.get(url)

        videos_in_template = list(response.context['videos'])
        self.assertEqual(videos_in_template, expected_video_order)

    # Tests to make sure that the no videos messages is being shown
    def test_no_video_message(self):
        url = reverse('video_list')
        response = self.client.get(url)

        self.assertContains(response, 'No videos.')
        self.assertEqual(0, len(response.context['videos']))


    def test_video_number_message_one_video(self):
        v1 = Video.objects.create(name='XYZ', notes='example', url='https://www.youtube.com/watch?v=123')
        url = reverse('video_list')
        response = self.client.get(url)

        self.assertContains(response, '1 video')
        self.assertNotContains(response, '1 videos')


    def test_video_number_message_two_videos(self):
        v1 = Video.objects.create(name='XYZ', notes='example', url='https://www.youtube.com/watch?v=123')
        v1 = Video.objects.create(name='XYZ', notes='example', url='https://www.youtube.com/watch?v=124')

        url = reverse('video_list')
        response = self.client.get(url)

        self.assertContains(response, '2 video')



class TestVideoSearch(TestCase):
    # search only shows matching videos, partial case-insensitive matches
    def test_video_search_matches(self):
        v1 = Video.objects.create(name='ABC', notes='example', url='https://www.youtube.com/watch?v=456')
        v2 = Video.objects.create(name='nope', notes='example', url='https://www.youtube.com/watch?v=789')
        v3 = Video.objects.create(name='abc', notes='example', url='https://www.youtube.com/watch?v=123')
        v4 = Video.objects.create(name='hello aBc!!!', notes='example', url='https://www.youtube.com/watch?v=101')
        
        expected_video_order = [v1, v3, v4]
        response = self.client.get(reverse('video_list') + '?search_term=abc')
        videos_in_template = list(response.context['videos'])
        self.assertEqual(expected_video_order, videos_in_template)


    def test_video_search_no_matches(self):
        v1 = Video.objects.create(name='ABC', notes='example', url='https://www.youtube.com/watch?v=456')
        v2 = Video.objects.create(name='nope', notes='example', url='https://www.youtube.com/watch?v=789')
        v3 = Video.objects.create(name='abc', notes='example', url='https://www.youtube.com/watch?v=123')
        v4 = Video.objects.create(name='hello aBc!!!', notes='example', url='https://www.youtube.com/watch?v=101')
        
        expected_video_order = []  # empty list 
        response = self.client.get(reverse('video_list') + '?search_term=kittens')
        videos_in_template = list(response.context['videos'])
        self.assertEqual(expected_video_order, videos_in_template)
        self.assertContains(response, 'No videos')
        

class TestVideoModel(TestCase):

    def test_create_id(self):
        video = Video.objects.create(name='example', url='https://www.youtube.com/watch?v=U8_umxNW_A4')
        self.assertEqual('U8_umxNW_A4', video.video_id)


    def test_create_id_valid_url_with_time_parameter(self):
        # a video that is playing and paused may have a timestamp in the query
        video = Video.objects.create(name='example', url='https://www.youtube.com/watch?v=5b5Bj2LF8xs&feature=youtu.be&t=86')
        self.assertEqual('5b5Bj2LF8xs', video.video_id)


    def test_create_video_notes_optional(self):
        v1 = Video.objects.create(name='example', url='https://www.youtube.com/watch?v=67890')
        v2 = Video.objects.create(name='different example', notes='example', url='https://www.youtube.com/watch?v=12345')
        expected_videos = [v1, v2]
        database_videos = Video.objects.all()
        self.assertCountEqual(expected_videos, database_videos)  # check contents of two lists/iterables but order doesn't matter.


    def test_invalid_url_raises_validation_error(self):
        invalid_video_urls = [
            'https://www.youtube.com/watch',
            'https://www.youtube.com/watch/somethingelse',
            'https://www.youtube.com/watch/somethingelse?v=1234567',
            'https://www.youtube.com/watch?abc=123',
            'https://www.youtube.com/watch?v=',
            'https://www.github.com',
            '12345678',
            'hhhhhhhttps://youtube.com/watch',
            'http://www.youtube.com/watch/somethingelse?v=1234567',
            'https://minneapolis.edu',
            'https://minneapolis.edu?v=123456'

        ]

        for invalid_video_url in invalid_video_urls:
            with self.assertRaises(ValidationError):
                Video.objects.create(name='example', url=invalid_video_url, notes='example note', )
        
        self.assertEqual(0, Video.objects.count())

    
    def test_duplicate_video_raises_integrity_error(self):
        v1 = Video.objects.create(name='XYZ', notes='example', url='https://www.youtube.com/watch?v=123')
        with self.assertRaises(IntegrityError):
            Video.objects.create(name='XYZ', notes='example', url='https://www.youtube.com/watch?v=123')

