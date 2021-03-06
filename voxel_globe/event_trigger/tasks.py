import os
from os import environ as env

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)
import logging

from voxel_globe.common_tasks import shared_task, VipTask

@shared_task(base=VipTask, bind=True)
def event_trigger(self, sattel_site_id):
  import voxel_globe.meta.models as models
  import betr_adaptor as betr
  import vil_adaptor_betr_batch as vil
  import vpgl_adaptor_betr_batch as vpgl
  
  site = models.SattelSite.objects.get(id=sattel_site_id)
  self.update_state(state="PROCESSING", meta={"site_name": site.name})
  event_triggers = site.satteleventtrigger_set.all()
  number_event_triggers= len(event_triggers)
  for event_trigger_index, etr in enumerate(event_triggers):
    event_geometries=etr.event_areas.all()
    number_event_geometries=len(event_geometries)
    for event_geometry_index, evt_obj in enumerate(event_geometries):

      if not etr.reference_areas.all():
        continue

      ref_obj = etr.reference_areas.all()[0] #REDO

      ref_image = etr.reference_image
      ref_cam = ref_image.camera_set.get(cameraset=site.camera_set).select_subclasses()[0] #REDO

      (ref_image_vil_msi, ni, nj) = vil.load_image_resource(ref_image.filename_path)
      ref_image_vil = vil.multi_plane_view_to_grey(ref_image_vil_msi)

      #(ref_image_vil, ni, nj) = vil.load_image_resource(ref_image.filename_path)
      ref_cam_vpgl = vpgl.load_rational_camera_from_txt(ref_cam.rpc_path)
      # print 'load rcam',status

      betr_etr = betr.create_betr_event_trigger(evt_obj.origin.x,evt_obj.origin.y,evt_obj.origin.z, 'rajaei_pier')
      print betr_etr.type

      rx = ref_obj.origin.x
      ry = ref_obj.origin.y
      rz = ref_obj.origin.z

      ex = evt_obj.origin.x
      ey = evt_obj.origin.y
      ez = evt_obj.origin.z
      betr.add_event_trigger_object(betr_etr, 'pier_ref',ex,ey,ez,ref_obj.geometry_path,True)
      betr.add_event_trigger_object(betr_etr, 'pier_evt',ex,ey,ez,evt_obj.geometry_path,False)
      
      images = site.image_set.images.all()
      number_images = len(images)
      for image_index, evt_image0 in enumerate(images):
        self.update_state(state="PROCESSING", meta={"site_name": site.name,
            "trigger": "{} out of {}".format(event_trigger_index+1,
                                             number_event_triggers),
            "geometry": "{} out of {}".format(event_geometry_index+1,
                                              number_event_geometries),
            "image": "{} out of {}".format(image_index+1, number_images)})
        (evt_image_vil_msi, ni, nj) =vil.load_image_resource(evt_image0.filename_path)
        evt_image_vil = vil.multi_plane_view_to_grey(evt_image_vil_msi)

        evt_cam = evt_image0.camera_set.get(cameraset=site.camera_set).select_subclasses()[0] #REDO
        evt_cam_vpgl = vpgl.load_rational_camera_from_txt(evt_cam.rpc_path)
        # print 'load rcam',status

        betr.set_event_trigger_data(betr_etr,ref_image_vil,ref_cam_vpgl, evt_image_vil, evt_cam_vpgl)
        
        score = betr.execute_event_trigger(betr_etr,'edgel_change_detection')
        print 'execute score(change)', score

        models.SattelEventResult(name="Event %s, %s, %s" % (site.name, evt_image0.name, evt_obj.name),
                                 geometry=evt_obj, score=score, 
                                 reference_image=ref_image,
                                 mission_image=evt_image0).save()

  return {"site_name": site.name}
