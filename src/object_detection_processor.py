"""
Copyright 2023 Sony Semiconductor Solutions Corp. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__),'.'))
sys.path.append(
    os.path.join(os.path.dirname(__file__),'smart_camera_interface_schema'))

import smart_camera_interface_schema.SmartCamera.BoundingBox as SBoundingBox
import smart_camera_interface_schema.SmartCamera.BoundingBox2d as SBoundingBox2d
import smart_camera_interface_schema.SmartCamera.ObjectDetectionTop as SObjectDetectionTop

class ObjectDetectionProcessor() :
    """Detect with ObjectDetection schema Interface Class

    """

    def __init__(self, config):
        raise NotImplementedError


    def __call__(self, serialize_meta):
        """detect main process

        Args:
            serialize_meta (bytes): serialized meta data

        """
        raise NotImplementedError


    def get_param_info(self):
        """Get parameter for other process

        """
        raise NotImplementedError


    def deserialize_meta_data(self, serialize_meta):
        """Deserialize input meta data

        schema of input meta data is SmartCamera.ObjectDetection

        Args:
            serialize_meta (bytes): serialized meta data

        Returns:
            list: deserialized meta data
        """

        array_meta = []
        if serialize_meta is not None:
            object_fb = SObjectDetectionTop.ObjectDetectionTop.GetRootAs(
                serialize_meta, 0)
            if object_fb.Perception() is not None:
                for i in range( object_fb.Perception().ObjectDetectionListLength()):
                    gen_obj = object_fb.Perception().ObjectDetectionList(i)
                    if gen_obj.BoundingBoxType() \
                        == SBoundingBox.BoundingBox().BoundingBox2d:
                        bounding_box2d = SBoundingBox2d.BoundingBox2d()
                        bounding_box2d.Init(
                            gen_obj.BoundingBox().Bytes, gen_obj.BoundingBox().Pos)
                        pos = [
                            bounding_box2d.Left(),
                            bounding_box2d.Top(),
                            bounding_box2d.Right(),
                            bounding_box2d.Bottom()
                        ]
                        conf = gen_obj.Score()
                        class_id = gen_obj.ClassId()
                        array_meta.append([pos,conf,class_id])
        return array_meta
