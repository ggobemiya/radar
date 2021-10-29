import socket
import binascii
import datetime
import cv2
import numpy as np

def msg_index(msg):    
    i = len(msg)
    if i//13 == 1:
        msg1 = [msg]
        j=0
        msgID = msg1[j][1]+msg1[j][0]
        return msg1, [msgID]
    else:
        msg1 = []
        msgID1 = []
        j=0
        while i != 13:
            split_msg, msg = msg[0:int(msg[4])+5],msg[int(msg[4])+5:]
            msg1 += [split_msg]
            msgID = split_msg[1]+split_msg[0]
            msgID1.append(msgID)
            i = len(msg)
        return msg1, msgID1

def str8(value):
    i = len(value)
    n = '0'*(8-i)+value
    return n

def hex2bin(value):
    n =bin(int(value,16))[2:]
    n = str8(n)
    return n

def bin2int(value):
    n=int(value,2)
    return n

def msg_ID(msg):
    msgID = msg[1]+msg[0]
    return msgID

def msg_reader(msg):
    i = len(msg)
    content = ''
    contents = []
    if i == 1:
        j=0
        content += hex2bin(msg[j][5])
        content += hex2bin(msg[j][6])
        content += hex2bin(msg[j][7])
        content += hex2bin(msg[j][8])
        content += hex2bin(msg[j][9])
        content += hex2bin(msg[j][10])
        content += hex2bin(msg[j][11])
        content += hex2bin(msg[j][12])
        return [content]
    else :
        for j in range(len(msg)):
            content += hex2bin(msg[j][5])
            content += hex2bin(msg[j][6])
            content += hex2bin(msg[j][7])
            content += hex2bin(msg[j][8])
            content += hex2bin(msg[j][9])
            content += hex2bin(msg[j][10])
            content += hex2bin(msg[j][11])
            content += hex2bin(msg[j][12])
            contents.append(content)
            content = ''
        return contents
    
def read_0x60B(msg):
    #object_general_information
    obj_ID = int(msg[0:8],2)
    obj_DistLong = round(int(msg[8:21],2)*0.2-500,3)
    obj_DistLat = round(int(msg[21:32],2)*0.2-204.6,3)
    obj_VrelLong = int(msg[32:42],2)*0.25-128
    obj_VrelLat = int(msg[42:51],2)*0.25-64
    obj_DynProp = int(msg[53:56],2)
    obj_RCS = int(msg[56:],2)*0.5-64
    return obj_ID, obj_DistLong, obj_DistLat, obj_VrelLong, obj_VrelLat, obj_DynProp, obj_RCS

if __name__ == '__main__':
    host = 'your IP'
    port = 10000
    s = socket.socket()
    s.connect((host,port))
    itera=0
    FOV = 60
    cam_height = 230
    cam_alpha = -3.7
    cam_beta = 30
    cam_width = 0.1
    obj_DistLong= ''
    f= open('coordi.txt','w')
    cap = cv2.VideoCapture("Your video address")
    if cap.isOpened() == False:
        print("can't open the CAM")
        exit()
    cv2.namedWindow('frame')
    a=700
    b=1200
    hei = 1920
    wid = 1080
    new_hei = 640
    new_wid = 360

    point_list1 = [(round(-250+a),round(abs(255-b))),(round(-250+a),round(abs(585-b))),(round(-500+a),round(abs(575-b)))]
    point_list2 = [(582/hei*new_hei,1034/wid*new_wid), (858/hei*new_hei, 575/wid*new_wid), (1344/hei*new_hei,497/wid*new_wid)]

    pts1 = np.float32([list(point_list1[0]),list(point_list1[1]),list(point_list1[2])])
    pts2 = np.float32([list(point_list2[0]),list(point_list2[1]),list(point_list2[2])])
    M = cv2.getAffineTransform(pts1,pts2)
    one_3 = np.array([1,1,1])
    one_1 = np.array([1])
    while itera<20000:
        ret, frame = cap.read()
        msg = s.recv(1024)
        byte_data = binascii.b2a_hex(msg,' ')
        str_data = byte_data.decode()
        msg1 = str_data.split(' ')
        msg2, msgID = msg_index(msg1)
        msg3 = msg_reader(msg2)
        data = ''
        if itera//100 ==0:
            if len(msg3) == 1 :
                if '060b' in msgID:
                    obj_ID, obj_DistLong, obj_DistLat, obj_VrelLong, obj_VrelLat, obj_DynProp, obj_RCS = read_0x60B(msg3[0])
                    print('113:', obj_ID, obj_DistLong, obj_DistLat, obj_VrelLong, obj_VrelLat, obj_DynProp, obj_RCS)
            else :
                for j in range(len(msg3)):
                    if '060b' in msgID[j]:
                        obj_ID, obj_DistLong, obj_DistLat, obj_VrelLong, obj_VrelLat, obj_DynProp, obj_RCS = read_0x60B(msg3[j])
                        print('120:',obj_ID, obj_DistLong, obj_DistLat, obj_VrelLong, obj_VrelLat, obj_DynProp, obj_RCS)
            if obj_DistLong != '':
                M2 = np.vstack([M,one_3])
                x = int(round(int(obj_DistLat)*100+a))
                y = int(round(abs(int(obj_DistLong)*100-b)))
                coordi = (x,y)
                ans = np.float32([list(coordi)])
                ans2 = np.reshape(ans,(2,1))
                ans3 = np.vstack([ans2,one_1])
                ans4 = M2.dot(ans3)
                x = int(round(ans4[0,0]))
                y = int(round(ans4[1,0]))
                print('coordi : ', x,y)
                cv2.circle(frame, (x, y), 10, (0, 0, 255), 10)
                obj_DistLong= ''
                obj_DistLat=''
        if cv2.waitKey(20) & 0xFF == ord('w'):
            cv2.imwrite('test.png',frame)
        frame = cv2.resize(frame,(new_hei,new_wid))
        cv2.imshow('frame', frame)
        height, width = frame.shape[:2]
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break
    itera +=1
cap.release()
cv2.destroyAllWindows()        
f.close()



