import os
#import voxel_globe.tasks as tasks
from ..common_tasks import app, VipTask
from glob import glob
import voxel_globe.meta.models
from os import environ as env
from os.path import join as path_join

from django.contrib.gis import geos

import subprocess;

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__);

@app.task(base=VipTask, bind=True)
def ingest_data(self, uploadSession_id, imageDir):
  ''' task for the ingest route, to ingest the data an upload sessions points to '''
  import voxel_globe.ingest.models as IngestModels
  import numpy
  from voxel_globe.tools.camera import saveKrt
  from PIL import Image

  uploadSession = IngestModels.UploadSession.objects.get(id=uploadSession_id);
  directories = uploadSession.directory.all();
  #imageDirectory = directories.filter(name='image')
  #metaDirectory = directories.filter(name='meta')

  imageCollection = voxel_globe.meta.models.ImageCollection.create(name="Generic Upload %s" % (uploadSession_id), service_id = self.request.id);
  imageCollection.save();

  r = numpy.eye(3);
  t = [0, 0, 0];
  
  gpsList = []
  
  for d in glob(os.path.join(imageDir, '*\\')):
    files = glob(os.path.join(d, '*.jpg'));
    files.sort()
    for f in files:
      self.update_state(state='PROCESSING', 
                        meta={'stage':'File %s of %d' % (f, len(files))})
      zoomifyName = f[:-4] + '_zoomify'
      pid = subprocess.Popen(['vips', 'dzsave', f, zoomifyName, '--layout', 'zoomify'])
      pid.wait();
      
      relFilePath = os.path.relpath(f, env['VIP_IMAGE_SERVER_ROOT']).replace('\\', '/');
      basename = os.path.split(f)[-1]
      relZoomPath = os.path.relpath(zoomifyName, env['VIP_IMAGE_SERVER_ROOT']).replace('\\', '/');
      
      image = Image.open(f)
      if image.bits == 8:
        pixel_format = 'b';
      if image.bits == 16:
        pixel_format = 's';
      if image.bits == 32:
        if image.mode == "I":
          pixel_format = 'i';
        elif image.mode == "F":
          pixel_format = 'f'

      img = voxel_globe.meta.models.Image.create(
                             name="Generic Upload %s Frame %s" % (uploadSession_id, basename), 
                             imageWidth=image.size[0], imageHeight=image.size[1], 
                             numberColorBands=image.layers, pixelFormat=pixel_format, fileFormat='zoom',
                             imageUrl='%s://%s:%s/%s/%s/' % (env['VIP_IMAGE_SERVER_PROTOCOL'], 
                                                             env['VIP_IMAGE_SERVER_HOST'], 
                                                             env['VIP_IMAGE_SERVER_PORT'], 
                                                             env['VIP_IMAGE_SERVER_URL_PATH'], 
                                                             relZoomPath),
                             originalImageUrl='%s://%s:%s/%s/%s' % (env['VIP_IMAGE_SERVER_PROTOCOL'], 
                                                                    env['VIP_IMAGE_SERVER_HOST'], 
                                                                    env['VIP_IMAGE_SERVER_PORT'], 
                                                                    env['VIP_IMAGE_SERVER_URL_PATH'], 
                                                                    relFilePath),
                             service_id = self.request.id);
      img.save();
     
      imageCollection.images.add(img);
      
      try:
        exifTags = image._getexif()
        gps = exifTags[34853]
      except:
        pass
      
      try:
        latitude = float(gps[2][0][0])/gps[2][0][1] + \
                   float(gps[2][1][0])/gps[2][1][1]/60.0 + \
                   float(gps[2][2][0])/gps[2][2][1]/3600.0;
        if gps[1] == 'N':
          pass;
        elif  gps[1] == 'S':
          latitude *= -1;
        else:
          latitude *= 0;
      except:
        latitude = 0;
        
      try:
        longitude = float(gps[4][0][0])/gps[4][0][1] + \
                    float(gps[4][1][0])/gps[4][1][1]/60.0 + \
                    float(gps[4][2][0])/gps[4][2][1]/3600.0;
        if gps[3] == 'W':
          longitude *= -1;
        elif  gps[3] == 'E':
          pass;
        else:
          longitude *= 0;
      except:
        longitude = 0;
        
      try:          
        altitude = float(gps[6][0])/gps[6][1]
        if gps[5] == '\x00':
          srid = 4326; #WGS84
        else:
          srid = 7428; #EGM 96
      except:
        altitude = 0;
        srid=4326;

      origin = [longitude, latitude, altitude];
      logger.error('Origin is: %s' % origin)
      if not any(numpy.array(origin) == 0):
        gpsList.append(origin);

      k = numpy.eye(3);
      k[0,2] = image.size[0]/2;
      k[1,2] = image.size[1]/2;      
      saveKrt(self.request.id, img, k, r, t, origin, srid=srid);
      
  averageGps = numpy.mean(numpy.array(gpsList), 0);
  
  voxel_globe.meta.models.Scene.create(name="Generic origin %s" % uploadSession_id, 
                                       service_id = self.request.id,
                                       origin='SRID=%d;POINT(%0.12f %0.12f %0.12f)' % \
                                       (srid, averageGps[0], averageGps[1], averageGps[2])).save()