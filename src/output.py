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

class Output() :
    """Output Interface Class

    """

    def __init__(self, config, image_info, param_info):
        raise NotImplementedError


    def __del__(self):
        raise NotImplementedError


    def __call__(self, dict_meta, image=None, timestamp=None):
        """output main process

        Args:
            dict_meta (dict): meta data
            image (numpy.ndarray, optional): image data. Defaults to None.
            timestamp (str, optional): timestamp string. Defaults to None.

        """
        raise NotImplementedError
