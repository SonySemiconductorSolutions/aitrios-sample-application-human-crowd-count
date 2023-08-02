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
import base64
import logging
import cv2
import numpy as np

import console_access_library
from console_access_library.client import Client
from console_access_library.common.config import Config
from console_access_library.common.read_console_access_settings import ReadConsoleAccessSettings

import data_loader


class ConsoleDataLoader(data_loader.DataLoader) :
    """load data from console

    Args:
        DataLoader (class): load data interface class
    """

    def __init__(self, config):

        # Init
        self._params = {}
        self._params['device_id'] = ''
        self._params['first_timestamp'] = ''
        self._params['last_timestamp'] = ''
        self._params['number_of_images'] = 0
        self._params['number_of_inference_results'] = 0
        self._image_time_list = []
        self._image_data_list = []
        self._meta_time_list = []
        self._meta_data_list = []
        self._console_access_client = None

        # Check parameter
        if not 'setting_path' in config:
            raise ValueError('Console Access Library setting file is not found')
        if not os.path.exists(config['setting_path']):
            raise ValueError(f"cannot open {config['setting_path']}")

        # Instantiate Console Access Library Client.
        console_access_library.set_logger(logging.INFO)

        read_console_access_settings_obj = ReadConsoleAccessSettings(config['setting_path'])
        config_obj = Config(
            read_console_access_settings_obj.console_endpoint,
            read_console_access_settings_obj.portal_authorization_endpoint,
            read_console_access_settings_obj.client_id,
            read_console_access_settings_obj.client_secret,
        )
 
        self._console_access_client = Client(config_obj)

        # Get parameter from config
        self._params['device_id'] = config['device_id']
        self._params['sub_directory_name'] = config['sub_directory_name']

        if isinstance(self._params['sub_directory_name'], str) \
            and self._params['sub_directory_name']:
            # metas and images
            self._params['number_of_images'] = config['number_of_images']
        else:
            # only metas
            self._params['number_of_inference_results'] \
                = config['number_of_inference_results']
            self._params['first_timestamp'] = config['first_timestamp']
            self._params['last_timestamp'] = config['last_timestamp']


    def __call__(self):
        """load data from console

        Returns:
            list: list of image data
            list: list of meta data
            list: list of timestamp
        """
        if isinstance(self._params['sub_directory_name'], str) \
            and self._params['sub_directory_name']:
            # get images and metas
            self._get_images()
            self._get_inference_results()
            self._match_image_and_meta()
        else:
            # get only metas
            self._get_inference_results()

        return self._image_data_list, self._meta_data_list, self._meta_time_list


    def get_image_info(self):
        """get image info for other process

        Returns:
            dict: infomation of image
        """
        image_info = {}

        if isinstance(self._params['sub_directory_name'], str) \
            and self._params['sub_directory_name']:
            image_info['image_flg'] = True
            image_info['image_name'] = self._params['sub_directory_name']
        else:
            image_info['image_flg'] = False
            image_info['image_name'] = None

        return image_info


    def _get_images(self):
        # get image response
        image_response = self._console_access_client.insight.get_images(
            self._params['device_id'],
            self._params['sub_directory_name'],
            self._params['number_of_images']
        )

        # check responce
        if isinstance(image_response, dict) and 'message' in image_response.keys():
            raise ValueError(f"{image_response['message']}")

        # number of images
        self._params['number_of_images'] = len(image_response['images'])

        for image_data in image_response['images']:

            # image timestamp
            self._image_time_list.append(image_data['name'].replace('.jpg', ''))

            # image data
            img_binary = base64.b64decode(image_data['contents'])
            img_arr = np.frombuffer(img_binary, dtype=np.uint8)
            self._image_data_list.append(
                cv2.imdecode(img_arr, flags=cv2.IMREAD_COLOR))


    def _get_inference_results(self):
        # with images
        if isinstance(self._params['sub_directory_name'], str) \
            and self._params['sub_directory_name']:
            if self._params['number_of_images'] > 0:
                self._params['first_timestamp'] = self._image_time_list[0]
                self._params['last_timestamp'] = self._image_time_list[-1]
                self._params['number_of_inference_results'] \
                    = self._params['number_of_images']
            else:
                self._params['number_of_inference_results'] = 0

        # filter setting
        if self._params['first_timestamp'] \
            or self._params['last_timestamp']:

            # fileter by timestamp
            filter_str = 'EXISTS(SELECT VALUE i FROM i IN c.Inferences WHERE '

            if not self._params['first_timestamp']:
                # filter by last timestamp
                last_timestamp = self._params['last_timestamp']
                filter_str += f'i.T <= "{last_timestamp}")'
            elif not self._params['last_timestamp']:
                # filter by first timestamp
                first_timestamp = self._params['first_timestamp']
                filter_str += f'i.T >= "{first_timestamp}")'
            else:
                # filter by first and last timestamp
                first_timestamp = self._params['first_timestamp']
                last_timestamp = self._params['last_timestamp']
                filter_str += \
                    f'i.T >= "{first_timestamp}" AND i.T <= "{last_timestamp}")'

            inference_response = \
                self._console_access_client.insight.get_inference_results(
                self._params['device_id'],
                number_of_inference_results=self._params['number_of_inference_results'],
                raw=1,
                filter=filter_str)
        else:
            inference_response = \
                self._console_access_client.insight.get_inference_results(
                self._params['device_id'],
                number_of_inference_results=self._params['number_of_inference_results'],
                raw=1)

        # check responce
        if isinstance(inference_response, dict) \
            and 'message' in inference_response.keys():
            raise ValueError(f"{inference_response['message']}")

        # get meta data from inference results
        for inference_data in inference_response:
            base64_data = inference_data['inference_result']['Inferences'][0]['O']
            fb_data = base64.b64decode(base64_data)
            time = inference_data['inference_result']['Inferences'][0]['T']
            self._meta_data_list.append(fb_data)
            self._meta_time_list.append(time)


    def _match_image_and_meta(self):
        match_meta_data_list = []

        # image timestamp loop
        for image_time in self._image_time_list:
            match_flag = False
            for meta_time, meta_data in zip(
                self._meta_time_list, self._meta_data_list):
                if meta_time == image_time:
                    match_meta_data_list.append(meta_data)
                    match_flag = True
                    break
            if match_flag is False:
                match_meta_data_list.append(None)

        # update meta data
        self._meta_data_list = match_meta_data_list
        self._meta_time_list = self._image_time_list
