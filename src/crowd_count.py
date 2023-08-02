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

import object_detection_processor

class CrowdCount(object_detection_processor.ObjectDetectionProcessor):
    """crowd counting class

    Args:
        ObjectDetectionProcessor (class):
        Detect with ObjectDetection schema Interface Class
    """
    MAX_AREA_NUM = 4
    MAX_POINT_NUM = 16
    DEBUG_CROWD_COUNT = False

    def __init__(self, config):
        self._stabilized_count = [0.0] * self.MAX_AREA_NUM
        self._initial = True
        self._inpolygon_params = {}
        self._stabilizer_params = {}
        self._remove_params = {}
        self._bbox2point_params = {}

        # load parameter from json
        self._inpolygon_params = config['inpolygon']
        self._stabilizer_params = config['stabilizer']
        self._remove_params = config['remove_low_conf']
        self._bbox2point_params = config['bbox2point']

        # parameter range check
        if self._inpolygon_params['area_num'] > self.MAX_AREA_NUM:
            raise RuntimeError(
                'area_num should be less than or equal to ', self.MAX_AREA_NUM)
        if len(self._inpolygon_params['area_point_len']) \
            < self._inpolygon_params['area_num']:
            raise RuntimeError(
                'size of \'area_point_len\' and area_num do not match.')
        if len(self._inpolygon_params['area_point']) \
            < self._inpolygon_params['area_num']:
            raise RuntimeError(
                'size of \'area_point\' and area_num do not match.')

        for area_num in range(self._inpolygon_params['area_num']):
            if self._inpolygon_params['area_point_len'][area_num] \
                > self.MAX_POINT_NUM:
                raise RuntimeError(
                    'area_point_len should be less than or equal to ', self.MAX_POINT_NUM
                )
            if self._inpolygon_params['area_point_len'][area_num] < 3:
                raise RuntimeError(
                    'area_point_len should be larger than 2 ')
            if len(self._inpolygon_params['area_point'][area_num]) \
                < self._inpolygon_params['area_point_len'][area_num]:
                raise RuntimeError(
                    'number of area_point should be larger than ',
                    self._inpolygon_params['area_point_len'][area_num]
                )



        if self._stabilizer_params['iir_down_ratio'] < 0 \
            or self._stabilizer_params['iir_down_ratio'] > 1:
            raise RuntimeError('iir_down_ratio must be set in the range of 0 to 1')
        if self._stabilizer_params['iir_up_ratio'] < 0 \
            or self._stabilizer_params['iir_up_ratio'] > 1:
            raise RuntimeError('iir_up_ratio must be set in the range of 0 to 1')

        if self.DEBUG_CROWD_COUNT:
            print(self._inpolygon_params)
            print(self._stabilizer_params)
            print(self._remove_params)
            print(self._bbox2point_params)

    def reset_iir(self):
        """reset iir stabilizer

        """
        self._stabilized_count = [0.0] * self.MAX_AREA_NUM
        self._initial = True

    def get_param_info(self):
        """get inpolygon parameter for other process

        """
        return self._inpolygon_params


    def __call__(self, serialize_meta):
        """crowd counting process

        Args:
            serialize_meta (bytes): serialized meta data

        Returns:
            dict: detect result
        """

        bbox_array = super().deserialize_meta_data(serialize_meta)

        bboxes, bboxes_score = self._remove_low_conf(bbox_array)
        positiones = self._bbox2point(bboxes)
        area_num, count = self._inpolygon(positiones)
        count_out = self._stabilizer(area_num, count)
        count_out = count_out[:area_num]

        # Output to dict
        result_dict = self.__output_to_dict(
            bboxes, bboxes_score, positiones, count_out)

        return result_dict


    def __output_to_dict(self, bboxes, bboxes_score, positiones, count_out):
        bbox_dicts = []
        for bbox in bboxes:
            bbox_dict = {
                'left': bbox[0],
                'top': bbox[1],
                'right': bbox[2],
                'bottom': bbox[3]
                }
            bbox_dicts.append(bbox_dict)

        position_dicts = []
        for position in positiones:
            position_dict = {
                'x': position[0],
                'y': position[1]
                }
            position_dicts.append(position_dict)

        result_dict = {
            'bboxes': bbox_dicts,
            'bboxes_score': bboxes_score,
            'positiones' : position_dicts,
            'count': count_out
        }

        return result_dict


    def debug_get_params(self):
        """get debug parameter

        """
        params = {}
        params['inpolygon'] = self._inpolygon_params
        params['stabilizer'] = self._stabilizer_params
        params['remove_low_conf'] = self._remove_params
        params['bbox2point'] = self._bbox2point_params

        return params

    def _remove_low_conf(self,detect_info):
        pre_bboxes = []
        pre_bboxes_score = []

        for info in detect_info:
            if info[1] >= self._remove_params['min_detect_score']:
                pre_bboxes.append(info[0])
                pre_bboxes_score.append(info[1])
            else:
                if self.DEBUG_CROWD_COUNT:
                    print('[remove_low_conf]:removed bbox:',info)

        bboxes = []
        bboxes_score = []

        for bbox, score in zip(pre_bboxes, pre_bboxes_score):
            max_th = self._remove_params['max_height']
            min_th = self._remove_params['min_height']

            height = bbox[3] - bbox[1]
            if min_th <= height <= max_th:
                bboxes.append(bbox)
                bboxes_score.append(score)
            else:
                if self.DEBUG_CROWD_COUNT:
                    print(f'[remove_low_conf]height:{height:d}')
                    print(f'[remove_low_conf]min_th:{min_th:f},max_th:{max_th:f}')

        return bboxes, bboxes_score

    def _bbox2point(self,bboxes):
        positiones = []
        ratio = self._bbox2point_params['bbox_to_point_ratio']
        for bbox in bboxes:
            position = [
                int((bbox[0] + bbox[2])/2.0), int(bbox[1]*(1.0-ratio) + bbox[3]*ratio)]
            positiones.append(position)
        return positiones

    def _inpolygon(self,positiones):
        area_num = self._inpolygon_params['area_num']
        area_point_len = self._inpolygon_params['area_point_len']
        area_point = self._inpolygon_params['area_point']

        count = [0.0] * self.MAX_AREA_NUM

        for area in range(area_num):
            polygon = area_point[area]
            num_len = area_point_len[area]
            if num_len < 3:
                print('ERROR: area_point_len should be larger than 2')
            for position in positiones:
                inside = False
                s_x = position[0]
                s_y = position[1]
                for i_1 in range(num_len):
                    i_2 = (i_1+1)%num_len
                    if min(polygon[i_1][0], polygon[i_2][0]) < s_x \
                        <= max(polygon[i_1][0], polygon[i_2][0]):
                        if (polygon[i_1][1] + (polygon[i_2][1]-polygon[i_1][1]) \
                            /(polygon[i_2][0]-polygon[i_1][0])*(s_x-polygon[i_1][0]) - s_y) \
                            > 0:
                            inside = not inside

                if inside:
                    count[area]+=1
        return area_num, count


    def _stabilizer(self, area_num, count):
        iir_down_ratio = self._stabilizer_params['iir_down_ratio']
        iir_up_ratio    = self._stabilizer_params['iir_up_ratio']

        val = 0.0
        count_out = [0] * self.MAX_AREA_NUM
        for area in range(area_num):
            val = 0.0
            current = count[area]
            previous = self._stabilized_count[area]
            if self._initial:
                val = current
                self._initial = False
            else:
                iir_ratio = 0.0
                if current > previous:
                    iir_ratio = iir_up_ratio
                else:
                    iir_ratio = iir_down_ratio
                val = previous * iir_ratio + current * (1.0 - iir_ratio)
            self._stabilized_count[area] = val
            count_out[area] = int(val+0.5)
            if count_out[area] < 0:
                count_out[area] = 0
        if self.DEBUG_CROWD_COUNT:
            print('[stabilizer] stabilized count:',self._stabilized_count)
        return count_out
