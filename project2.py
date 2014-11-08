import os
import urllib
import time

from google.appengine.api import users
from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class BlobFile(db.Model):
    #key = db.StringProperty()
    content = db.BlobProperty()

class MainPage(webapp2.RequestHandler):
    def get(self):

        user = users.get_current_user()
        if user:
            url_link = users.create_logout_url(self.request.uri)
        else:
            self.redirect(users.create_login_url(self.request.uri))
            return

        upload_url = blobstore.create_upload_url('/upload')

        audio_data = blobstore.BlobInfo.all().filter('content_type >= ', 'audio').filter('content_type <=', u"audio" + u"\ufffd")
        video_data = blobstore.BlobInfo.all().filter('content_type >= ', 'video').filter('content_type <=', u"video" + u"\ufffd")
        image_data = blobstore.BlobInfo.all().filter('content_type >= ', 'image').filter('content_type <=', u"image" + u"\ufffd")

        #index_list = all_data.index_list()
        blob_data =  {'test': 123, 'XXX': 456, 'KKK': 789}
        template_values = {
            'UserName': user.nickname(),
            'SignoutURL': url_link,
            'UploadURL': upload_url,
            'AudioTable': audio_data,
            'VideoTable': video_data,
            'ImageTable': image_data,
            'ImageAPI': images,
        }

        template = JINJA_ENVIRONMENT.get_template('html/index.html')
        self.response.write(template.render(template_values))

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        time.sleep(0.1)
        self.redirect('/')

#class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
#    def get(self, resource):
#        resource = str(urllib.unquote(resource))
#        blob_info = blobstore.BlobInfo.get(resource)
#        self.send_blob(blob_info)
class ServeHandler(webapp2.RequestHandler):
    def get(self, resource):

        user = users.get_current_user()
        if user:
            url_link = users.create_logout_url(self.request.uri)
        else:
            self.redirect(users.create_login_url(self.request.uri))
            return
        
        resource = str(urllib.unquote(resource))
        imageURL = images.get_serving_url(resource)
        blob_info = blobstore.BlobInfo.get(resource)
        image = images.Image(blob_key=resource)
        image.im_feeling_lucky() # do a transform, otherwise GAE complains.
        image.execute_transforms(output_encoding=images.PNG,quality=1)

        #self.response.write(imageURL)

        template_values = {
            'UserName': user.nickname(),
            'SignoutURL': url_link,
            'imageURL': imageURL,
            'imageWidth': image.width,
            'imageHeight': image.height,
            'imageFormat': blob_info.content_type,
            'imageKey': resource,
        }

        template = JINJA_ENVIRONMENT.get_template('html/image.html')
        self.response.headers.add('Content-Encoding', 'gzip')
        self.response.write(template.render(template_values))


class RotateHandler(webapp2.RequestHandler):
    def post(self, resource):
        user = users.get_current_user()
        if user:
            url_link = users.create_logout_url(self.request.uri)
        else:
            self.redirect(users.create_login_url(self.request.uri))
            return

        resource = str(urllib.unquote(resource))
        image = images.Image(blob_key=resource)
        degree = self.request.get("degree")
        image.im_feeling_lucky()
        image.rotate(int(degree))
        newimage = image.execute_transforms(output_encoding=images.JPEG)

        newblobFile = BlobFile(content=newimage)
        newblobFile.put()

        img_url = "/img?img_id={}".format(newblobFile.key())

        template_values = {
            'UserName': user.nickname(),
            'SignoutURL': url_link,
            'imageURL': img_url,
        }
        template = JINJA_ENVIRONMENT.get_template('html/newimage.html')
        self.response.write(template.render(template_values))
        return

    def get(self, resource):
        self.redirect('/')
        return

class ChopHandler(webapp2.RequestHandler):
    def post(self, resource):
        
        user = users.get_current_user()
        if user:
            url_link = users.create_logout_url(self.request.uri)
        else:
            self.redirect(users.create_login_url(self.request.uri))
            return

        resource = str(urllib.unquote(resource))
        image = images.Image(blob_key=resource)
        image.im_feeling_lucky() # do a transform, otherwise GAE complains.
        image.execute_transforms(output_encoding=images.PNG,quality=1)
        print self.request.get("x1")
        left = float(self.request.get("x1"))/image.width
        top = float(self.request.get("y1"))/image.height
        right = float(self.request.get("x2"))/image.width
        bottom = float(self.request.get("y2"))/image.height

        image.crop(float(left), float(top), float(right), float(bottom))
        newimage = image.execute_transforms(output_encoding=images.JPEG)

        newblobFile = BlobFile(content=newimage)
        newblobFile.put()

        img_url = "/img?img_id={}".format(newblobFile.key())
        template_values = {
            'UserName': user.nickname(),
            'SignoutURL': url_link,
            'imageURL': img_url,
        }
        template = JINJA_ENVIRONMENT.get_template('html/newimage.html')
        self.response.write(template.render(template_values))
        return

    def get(self, resource):
        self.redirect('/')
        return

class ImageHandler(webapp2.RequestHandler):
    def get(self):
        imgfile = db.get(self.request.get('img_id'))
        if imgfile.content:
            self.response.headers['Content-Type'] = 'image/jpeg'
            self.response.out.write(imgfile.content)
        else:
            self.response.out.write('No image')

class DeleteHandler(webapp2.RequestHandler):
    def get(self):
        file_key = self.request.get('delete_id')
        file_info = blobstore.BlobInfo.get(file_key)
        file_info.delete()
        self.redirect('/')

class fileHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)

class ThumbHandler(webapp2.RequestHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        thumburl = images.get_serving_url(blob_key=resource)


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/rotate/([^/]+)?', RotateHandler),
    ('/crop/([^/]+)?', ChopHandler),
    ('/delete', DeleteHandler),
    ('/upload', UploadHandler),
    ('/img', ImageHandler),
    ('/file/([^/]+)?', fileHandler),
    ('/thumb/([^/]+)?', ThumbHandler),
    ('/serve/([^/]+)?', ServeHandler)],
    debug=True)