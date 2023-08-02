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

class DataLoader() :
    """load data interface class

    """
    def __init__(self, config):
        raise NotImplementedError

    def __call__(self):
        """load data main process

        """
        raise NotImplementedError


    def get_image_info(self):
        """get image info for other process

        """
        raise NotImplementedError
