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
import ast
import pandas as pd
import cv2
import flatbuffers

import data_loader

sys.path.append(os.path.join(os.path.dirname(__file__),'.'))
sys.path.append(
    os.path.join(os.path.dirname(__file__),'smart_camera_interface_schema'))

import smart_camera_interface_schema.SmartCamera.BoundingBox as SBoundingBox
import smart_camera_interface_schema.SmartCamera.BoundingBox2d as SBoundingBox2d
import smart_camera_interface_schema.SmartCamera.GeneralObject as SGeneralObject
import smart_camera_interface_schema.SmartCamera.ObjectDetectionData as SObjectDetectionData
import smart_camera_interface_schema.SmartCamera.ObjectDetectionTop as SObjectDetectionTop

class LocalDataLoader(data_loader.DataLoader) :
    """load data from local file

    Args:
        DataLoader (class): load data interface class
    """

    def __init__(self, config):

        # Init
        self._video_file = ''
        self._meta_file = ''
        self._image_data_list = []
        self._meta_data_list = []
        self._meta_time_list = []

        # Get parameter from config
        self._video_file = config['video_file']
        self._meta_file = config['meta_file']

    def __call__(self):
        """load data from local file

        Returns:
            list: list of image data
            list: list of meta data
            list: list of timestamp
        """

        # get images from video file
        if isinstance(self._video_file, str) and self._video_file:
            self._get_images()

        # get meta datas from text file
        self._get_meta_data_list()

        return self._image_data_list, self._meta_data_list, self._meta_time_list


    def get_image_info(self):
        """get image info for other process

        Returns:
            dict: infomation of image
        """

        image_info = {}

        if isinstance(self._video_file, str) and self._video_file:
            # input images
            image_info['image_flg'] = True
            basename = os.path.basename(self._video_file)
            image_info['image_name'] = os.path.splitext(basename)[0]
        else:
            # no input image
            image_info['image_flg'] = False
            image_info['image_name'] = None

        return image_info


    def _get_images(self):

        cap = cv2.VideoCapture(self._video_file)

        # open video check
        if not cap.isOpened():
            raise ValueError(f'cannot open {self._video_file}')

        # get image data from video
        while True:
            ret, frame = cap.read()

            if ret:
                self._image_data_list.append(frame)
            else:
                break


    def _get_meta_data_list(self):

        # file check
        if not os.path.exists(self._meta_file):
            raise ValueError(f'cannot open {self._meta_file}')

        # read meta data from csv file
        # Column 1 is frame number
        # Column 2 is inference result string
        data_frame = pd.read_csv(self._meta_file, index_col=0)

        # csv loop
        for _, row_data in data_frame.iterrows():
            # Extract inference data
            str_meta = row_data.values.tolist()[0]
            # string to dictionary
            dict_meta = ast.literal_eval(str_meta)

            # dictionary to flatbuffers
            serialize_meta = self._serialize_meta_data(dict_meta)
            self._meta_data_list.append(serialize_meta)

    def _serialize_meta_data(self, dict_meta):
        general_obj_list = []
        builder = flatbuffers.Builder(0)
        for dict_general_object in dict_meta['perception']['object_detection_list']:
            SBoundingBox2d.Start(builder)
            SBoundingBox2d.AddLeft(
                builder, dict_general_object['bounding_box']['left'])
            SBoundingBox2d.AddTop(
                builder, dict_general_object['bounding_box']['top'])
            SBoundingBox2d.AddRight(
                builder, dict_general_object['bounding_box']['right'])
            SBoundingBox2d.AddBottom(
                builder, dict_general_object['bounding_box']['bottom'])
            body_bounding_box_fbs = SBoundingBox2d.End(builder)

            SGeneralObject.Start(builder)
            SGeneralObject.AddClassId(builder, dict_general_object['class_id'])
            SGeneralObject.AddBoundingBoxType(
                builder, SBoundingBox.BoundingBox().BoundingBox2d)
            SGeneralObject.AddBoundingBox(builder, body_bounding_box_fbs)
            SGeneralObject.AddScore(
                builder, dict_general_object['score'])
            general_obj = SGeneralObject.End(builder)
            general_obj_list.append(general_obj)

        SObjectDetectionData.StartObjectDetectionListVector(
            builder, len(general_obj_list))
        for counted_general_obj in general_obj_list:
            builder.PrependUOffsetTRelative(counted_general_obj)
        counted_general_obj_list_fb = builder.EndVector(len(general_obj_list))

        SObjectDetectionData.Start(builder)
        SObjectDetectionData.AddObjectDetectionList(
            builder, counted_general_obj_list_fb)
        object_buf = SObjectDetectionData.End(builder)

        SObjectDetectionTop.Start(builder)
        SObjectDetectionTop.AddPerception(builder, object_buf)
        buf = SObjectDetectionTop.End(builder)
        builder.Finish(buf)

        serialize_meta = builder.Output()

        return serialize_meta
