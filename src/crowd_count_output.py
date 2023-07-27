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
import json
import cv2

import output

class CrowdCountOutput(output.Output) :
    """Output Class for Crowd Count

    Args:
        Output (class): Output interface class
    """

    def __init__(self, config, image_info, param_info):
        # Init
        self._counter = 0

        # Get config param
        output_dir = config['output_dir']
        self._output_video = image_info['image_flg']

        # Make output json directory
        self._json_output_dir = os.path.join(output_dir, 'detect/')
        os.makedirs(self._json_output_dir, exist_ok=True)

        # Output video setting
        if self._output_video is True:
            video_output_dir = os.path.join(output_dir, 'video/')
            os.makedirs(video_output_dir, exist_ok=True)

            output_name = image_info['image_name']
            frame_rate = config['output_video_fps']
            self._width = config['output_video_width']
            self._height = config['output_video_height']

            video_file_name = video_output_dir + output_name + '_crowd_count.mp4'
            fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
            self._video_writer = cv2.VideoWriter(
                video_file_name, fourcc, frame_rate, (self._width, self._height)
            )

            self._param_info = {}
            self._param_info['area_point_len'] = param_info['area_point_len']
            self._param_info['area_point'] = param_info['area_point']
            self._param_info['area_num'] = param_info['area_num']

    def __del__(self):
        if self._output_video is True:
            self._video_writer.release()


    def __call__(self, dict_meta, image=None, timestamp=None):
        """output crowd count result

        Args:
            dict_meta (dict): meta data
            image (numpy.ndarray, optional): image data. Defaults to None.
            timestamp (str, optional): timestamp string. Defaults to None.
        """

        # add timestamp for json output
        if timestamp is not None:
            dict_meta['timestamp'] = timestamp

        # output json
        if timestamp is not None:
            json_file_name = timestamp
        else:
            json_file_name = f'{self._counter:08d}'
            self._counter += 1

        with open(
                self._json_output_dir + json_file_name + '.json', 'w', encoding='utf-8'
            ) as file:
            json.dump(dict_meta, file, indent=4)

        # output movie
        if self._output_video is True and image is not None:

            font_scale = min(self._width, self._height) * 0.001 

            for polygon, num_len \
                in zip(
                self._param_info['area_point'], self._param_info['area_point_len']):
                for i in range(num_len-1):
                    cv2.line(image,
                        (polygon[i][0], polygon[i][1]),
                        (polygon[i+1][0], polygon[i+1][1]),
                        (0, 255, 0), thickness=4
                    )
                cv2.line(image,
                    (polygon[0][0], polygon[0][1]),
                    (polygon[num_len-1][0], polygon[num_len-1][1]),
                    (0, 255, 0), thickness=4
                )


            for bbox, score in zip(dict_meta['bboxes'], dict_meta['bboxes_score']):
                cv2.rectangle(
                    image,(bbox['left'],bbox['top']),
                    (bbox['right'],bbox['bottom']),
                    (0,0,255),2
                )
                cv2.putText(
                    image, f'{int(score*100)}%', (bbox['left'], bbox['top']-8),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,0,255), 1, cv2.LINE_AA
                )

            for position in dict_meta['positiones']:
                cv2.drawMarker(image,
                    position=[position['x'], position['y']],
                    color=(0, 255, 0),
                    markerType=cv2.MARKER_CROSS,
                    markerSize=20,
                    thickness=2,
                    line_type=cv2.LINE_4
                )

            for area in range(self._param_info['area_num']):
                text='Count(area'+str(area+1)+'):'+str(dict_meta['count'][area])
                (text_width, text_height), baseline = cv2.getTextSize(
                    text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 0
                ) 
                cv2.putText(
                    image, text, (5,((2*text_height)*(area+1))),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,225,0), 1, cv2.LINE_AA
                )

            if timestamp is not None:
                timestamp_text=timestamp[:4]+'-'+timestamp[4:6]+'-'+timestamp[6:8] \
                            +' '+timestamp[8:10]+':'+timestamp[10:12]+':'+timestamp[12:14]
                cv2.putText(
                    image, timestamp_text, (5, self._height-(2*text_height)),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0,225,0), 1, cv2.LINE_AA
                )

            # write video
            image = cv2.resize(image, (self._width, self._height))
            self._video_writer.write(image)
