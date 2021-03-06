from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader

def tiepoint_registration_1(request):
  from voxel_globe.meta import models
  image_set_list = models.ImageSet.objects.all()
  return render(request, 'tiepoint_registration/html/tiepoint_registration_1.html', 
                {'image_set_list':image_set_list})

def tiepoint_registration_2(request, image_set_id):
  from voxel_globe.meta import models
  camera_set_list = models.ImageSet.objects.get(id=image_set_id).cameras.all()
  return render(request, 'tiepoint_registration/html/tiepoint_registration_2.html', 
                {'camera_set_list':camera_set_list,
                 'image_set_id':image_set_id})

def tiepoint_registration_3(request, image_set_id, camera_set_id):
  from voxel_globe.tiepoint_registration import tasks

  image_set_id = int(image_set_id)
  
  t = tasks.tiepoint_registration.apply_async(args=(image_set_id,camera_set_id), user=request.user)
  
  return render(request, 'tiepoint_registration/html/tiepoint_registration_3.html',
                {'task_id': t.task_id})
  
def tiepoint_error_1(request):
  from voxel_globe.meta import models
  image_set_list = models.ImageSet.objects.all()
  return render(request, 'tiepoint_registration/html/tiepoint_error_1.html', 
                {'image_set_list':image_set_list})

def tiepoint_error_2(request, image_set_id):
  from voxel_globe.meta import models
  camera_set_list = models.ImageSet.objects.get(id=image_set_id).cameras.all()
  return render(request, 'tiepoint_registration/html/tiepoint_error_2.html', 
                {'camera_set_list':camera_set_list,
                 'image_set_id':image_set_id})


def tiepoint_error_3(request, image_set_id, camera_set_id):
  from voxel_globe.meta import models
  scene_list = models.Scene.objects.all()
  return render(request, 'tiepoint_registration/html/tiepoint_error_3.html',
                {'scene_list':scene_list,
                 'camera_set_id':camera_set_id,
                 'image_set_id':image_set_id})

def tiepoint_error_4(request, image_set_id, camera_set_id, scene_id):
  from voxel_globe.tiepoint_registration import tasks

  image_set_id = int(image_set_id)
  
  t = tasks.tiepoint_error_calculation.apply_async(args=(image_set_id,
                                                         camera_set_id,
                                                         scene_id),
                                                   user=request.user)
  
  return render(request, 'tiepoint_registration/html/tiepoint_error_4.html',
                {'task_id': t.task_id})
  
def order_status(request, task_id):
  from celery.result import AsyncResult
  
  task = AsyncResult(task_id)

  return render(request, 'task/html/task_3d_error_results.html',
                {'task': task})