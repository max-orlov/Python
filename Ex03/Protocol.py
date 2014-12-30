__author__ = 'Alon Ben-Shimol'


import socket
import time

END_MSG = "$$"
TIME_OUT_TIME = 2  # DO NOT CHANGE


class NetworkErrorCodes():

    SUCCESS = 0
    FAILURE = 1
    DISCONNECTED = 2


    def __init__(self):
        pass



def send_all(s, msg):
    """
    This method is user in order to send the message 'msg' into the remote-end
    connected to the socket 's'. The message should be sent as a string.
    
    In case of success: [NetworkErrorCodes.SUCCESS, None] is returned.
    
    This method could fail from 2 reasons, either a time out, or general socket.error.
    In both case NetworkErrorCodes.FAILURE is returned to the called, where a string
    containing the message info is also returned to the sender.
    """

    s.settimeout(TIME_OUT_TIME)
    time.sleep(0.1)
    try:
        s.sendall(msg + END_MSG)
    
    except socket.error as e:
        return [NetworkErrorCodes.FAILURE, 'ERROR - Could not send message: %s.\n' % e[0]]

    except socket.timeout:
        return [NetworkErrorCodes.FAILURE, 'ERROR: TIMED-OUT.\n']

    return [NetworkErrorCodes.SUCCESS, None]



def recv_all(s):
    """
    This method is used in order to recieve a message sent through the remove-end socket
    connected to s. The message recieved as string.
    
    This method is blocking until the entire message from the remote end is sent.
    
    On success:  NetworkErrorCodes.SUCCESS is returned, and the actual data will also
    be returned to the caller (as a string).
    
    Upon failure NetworkErrorCodes.FAILURE will be returned with the appropriate error message.
    
    In case the remove end has closed its connection, NetworkErrorCodes.DISCONNECTED is 
    returned.
    
    """

    s.settimeout(TIME_OUT_TIME)
    time.sleep(0.1)
    all_data = ''

    while True:

        try:
            data = s.recv(4096)  # DO NOT CHANGE

        except socket.error as e:
            return [NetworkErrorCodes.FAILURE, 'ERROR - Could not recieve a message: %s.\n' % e[0]]

        except socket.timeout:
            return [NetworkErrorCodes.FAILURE, 'ERROR: TIMED-OUT.\n']

        all_data += data
        if len(all_data) == 0:
            return [NetworkErrorCodes.DISCONNECTED, ""]

        if all_data.endswith(END_MSG):  
            return [NetworkErrorCodes.SUCCESS, all_data[:-len(END_MSG)]]