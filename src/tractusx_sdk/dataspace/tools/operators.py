#################################################################################
# Eclipse Tractus-X - Software Development KIT
#
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the
# License for the specific language govern in permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0
#################################################################################

## Authorization Managment from Eclipse Tractus-X Simple Wallet 
## Author: Mathias Brunkow Moser
## License: Apache License, Version 2.0
## Source: https://github.com/eclipse-tractusx/digital-product-pass/blob/main/dpp-verification/simple-wallet/utilities/operators.py
## Extended here with some additional functionality

# Set log levels
from shutil import copyfile, move
import shutil
import os
import sys
import json
import time
import io

from datetime import datetime, timezone

"""
Class that defines operations in files, directories, clases, ...
"""
class op:
   
    @staticmethod
    def json_string_to_object(json_string: str | bytes | bytearray):
        """
            Method to convert a JSON string into a python object
                Accepts: json_string: source JSON string in string, bytes or bytearray
                Returns: Python object
                Raises: 
                    -JSONDecodeError if the JSON string is not valid
                    -TypeError if the arg is not a valid JSON format
        """
        data = json.loads(s=json_string)
        return data

    
    @staticmethod
    def to_json(source_object,indent:int=None,ensure_ascii:bool=True):
        """
            Method to convert a python object to a JSON string
                Accepts: obj:Source object in serializable formats (not sets, custom objects or bytes)
                         indent: Indentation level for pretty-printing
                         ensure_ascii: If False, escape non-ASCII characters with \\uXXXX
                Returns: resulting JSON string
                Raises: 
                    -TypeError if the obj arg is not a valid serializable object
        """
        return json.dumps(obj=source_object,indent=indent,ensure_ascii=ensure_ascii)
    
    @staticmethod
    def to_json_file(source_object,json_file_path:str,file_open_mode:str="w",indent:int=2):
        """
            Method to write a python object to a JSON file
                Accepts: obj: Source object in serializable formats
                         json_file_path: Destination file path
                         file_open_mode: Open mode for file
                         indent: Indentation level for pretty-printing
                Returns: None
                Raises:
                    -ValueError: if file_open_mode is invalid
                    -TypeError: if object is not serializable into JSON
        """
        tmp_json_string=op.to_json(source_object=source_object,indent=indent)
        op.write_to_file(data=tmp_json_string, file_path=json_file_path,open_mode=file_open_mode, end="")
        
    @staticmethod
    def read_json_file(file_path,encoding:str="utf-8"):
        """
            Method to read a JSON file and return its content as a python object
                Accepts: file_path: Path to the JSON file
                         encoding: Encoding of the file
                Returns: Deserialized JSON object
                Raises:
                    - FileNotFoundError: if the file does not exist
                    - JSONDecodeError: if the file is not a valid JSON file
        """
        data=None
        f = open(file_path,"r",encoding=encoding)
        data = json.load(f)
        f.close()
        
        return data  

    @ staticmethod
    def path_exists(file_path):
        """
            Method to check if a file or directory exists
                Accepts: file_path: Path to the file or directory
                Returns: True if the file or directory exists, False otherwise
        """
        return os.path.exists(file_path)

    @ staticmethod
    def make_dir(dir_name, permits=0o777) -> bool:
        """
            Method to create a directory
                Accepts: dir_name: Name of the directory
                         permits: Permission bits for the directory
                Returns: True if the directory is correctly created, False otherwise
        """
        if not op.path_exists(dir_name):
            os.makedirs(dir_name, permits)
            return True
        return False
    
    
    @ staticmethod
    def delete_dir(dir_name) -> bool:
        """
            Method to delete a directory
                Accepts: dir_name: Name of the directory
                Returns: True if the directory was successfully deleted, False otherwise
        """
        try:
            shutil.rmtree(dir_name)
            return True
        except Exception as e:
            return False
    
    """
    Wrappers in snake_case convention for copying files and moving them.
    """
    @ staticmethod
    def copy_file(file_path, dst):
        """
            Wrapper method to copy a file to a destination
                Accepts: file_path: Source file path
                         dst: Destination file path
                Returns: Destination route after file copied
        """
        return copyfile(file_path, dst)

    @ staticmethod
    def move_file(file_path, dst):
        """
            Wrapper method to move a file to a destination
                Accepts: file_path: Source file path
                         dst: Destination file path
                Returns: Destination rout after file moved
        """
        return move(file_path, dst)

    @ staticmethod
    def to_string(file_path, open_mode:str="r", encoding=sys.stdout.encoding):
        """
            Method to read a file and return its content as a string
                Accepts: file_path: Path to the file
                         open_mode: Open mode for file
                         encoding: Encoding of the file
                Returns: File content as a string
                Raises:
                    - FileNotFoundError: if the file does not exist
                    - IOError: if the file cannot be opened
        """
        if "b" in open_mode: #If reading binary, encoding arg not supported
            with open(file_path, open_mode) as f:
                string = f.read()
        else:
            with open(file_path, open_mode, encoding=encoding) as f:
                string = f.read()
        return string
    
    @ staticmethod
    def load_file(file_path) -> io.BytesIO:
        """
            Method to load a file from the filesystem and return the contents as a buffer
                Accepts: file_path: Path to the file
                Returns: File contents as a buffer
                Raises:
                - FileNotFoundError: if the file does not exist
                - IOError: if the file cannot be opened
                - PermissionError: if the file cannot be opened due to permissions
        """
        with open(file_path, "rb") as f:
            buffer_file = f.read()
        buffer = io.BytesIO(buffer_file)
        return buffer

    @ staticmethod
    def delete_file(file_path) -> bool:
        """
            Method to delete a file from the filesystem
                Accepts: file_path: Path to the file
                Returns: True if the file was deleted successfully, False otherwise
                Raises:
                - PermissionError/IsADirectoryError: if the file cannot be deleted due to permissions or is a directory
        """
        if not op.path_exists(file_path):
            return False

        os.remove(file_path)
        return True
    
    @staticmethod
    def timestamp(zone=timezone.utc, string=False):
        """
            Method to get the current timestamp according to the specified zone
                Accepts: zone: The timezone to get the timestamp from
                        string: If True, the timestamp will be returned as a string, otherwise as a float
                Returns: The current timestamp in the specified timezone
        """
        timestamp = datetime.timestamp(datetime.now(zone))
        if (string):
            return str(timestamp)
        return timestamp
    
    @staticmethod
    def get_filedatetime(zone=timezone.utc):
        """
            Method to get the current time according to the specified zone
                Accepts: zone: The timezone to get the timestamp from
                Returns: The current time in the specified timezone in the format "YYYY-MM-DD HH:MM:SS"
        """
        return datetime.now(zone).strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def get_filedate(zone=timezone.utc):
        """
            Method to get the current date according to the specified zone
                Accepts: zone: The timezone to get the timestamp from
                Returns: The current date in the specified timezone in the format "YYYYMMDD"
        """
        return datetime.now(zone).strftime("%Y%m%d")

    @ staticmethod
    def get_path_without_file(file_path):
        """
            Wrapper method to get the directory path of a file
                Accepts: file_path: Path to the file
                Returns: The directory path of the file
        """
        return os.path.dirname(file_path)

    @ staticmethod
    def write_to_file(data, file_path, open_mode:str="r", end:str="") -> bool:
        """
            Method to write data to a file
                Accepts: data: Data to be written
                         file_path: Destination file path
                         open_mode: Open mode for file
                         end: Additional characters to be appended at the end of the file
                Returns: True if the data was written successfully, False otherwise
                Raises:
                - FileNotFoundError: if the file cannot be opened
                - PermissionError: if the file cannot be opened due to permissions
                - ValueError: if the open mode is not valid
        """
        if(data == "" or data is None):
            return False

        with open(file_path, open_mode, encoding=sys.stdout.encoding) as file:
            file.write(data)
            file.write(end)
        
        return True
    
    @staticmethod
    def wait(seconds):
        """
            Wrapper method to sleep for some seconds
            Accepts: seconds: Number of seconds to sleep
            Returns: None
        """
        return time.sleep(seconds)
    
    @staticmethod
    def get_attribute(source_object:str,attr_path:str,default_value=None,path_sep:str="."):
        """
            Method to retrieve an attribute from a nested JSON object
                Accepts: source_object: JSON object
                         attr_path: Path to the attribute
                         default_value: Default value to be returned if the attribute does not exis
                         path_sep: Separator for the attribute path
                Returns: The value of the attribute if it exists, otherwise the default value
                Raises:
                - TypeError: if the source_object is not subscriptable
        """
        tmp_ret=default_value
        if source_object is None:
            return tmp_ret
    
        if path_sep is None or path_sep == "":
            return tmp_ret
    
        tmp_parts=attr_path.split(path_sep)
        if tmp_parts is None or tmp_parts == [""]:
            return tmp_ret
        for part in tmp_parts:
            if part not in source_object:
                return tmp_ret
            source_object=source_object[part]
        tmp_ret=source_object
        return tmp_ret
