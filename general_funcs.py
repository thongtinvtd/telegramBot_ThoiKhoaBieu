from constants import hostDB, userDB, passDB, dataDB, TOKEN_TL
import mysql.connector
import sys
import os
import requests
import json
import re
import lxml.html as html
from datetime import datetime

# # Connect database
# conn = mysql.connector.connect(
#     host=hostDB,
#     user=userDB,
#     password=passDB,
#     database=dataDB
# )
# curs = conn.cursor()
# print("Connect DB successful!")


def get_id_giaovien(name):
    try:
        url = "https://ems.vlute.edu.vn/api/danhmuc/getgiangvienbykeyword/{}"
        data = requests.get(url.format(name))
        print('getgiangvienbykeyword:', data.text)
        datajson = json.loads(data.text)
        return datajson
    except Exception as e:
        print("Error get_id_giaovien", e)
        datajson = []


def get_ma_hocky():
    url_mahocky = "https://ems.vlute.edu.vn/api/danhmuc/getdshocky"
    try:
        data_mahocky = requests.get(url_mahocky)
        data = data_mahocky.json()
        # print('data_mahocky', data)
        if data_mahocky.status_code == 200:
            # lấy mã của học kỳ cuối cùng - phần tử đầu tiên
            return data[0]['id']
        else:
            return 0
    except Exception as e:
        print('Error get ma_hocky:', e)


def get_schedule(id_giaovien, hocky):
    url_tkb = "https://ems.vlute.edu.vn/vTKBGiangVien/ViewTKBGV?hocky={}&magv={}"
    try:
        data_tkb = requests.post(url_tkb.format(hocky, id_giaovien))
        # print(data_tkb.text)
        if data_tkb.status_code == 200:
            return data_tkb
        else:
            return None
    except Exception as e:
        print('Error get_schedule:', e)


patterns_kodau = {
    '[àáảãạăắằẵặẳâầấậẫẩ]': 'a',
    '[đ]': 'd',
    '[èéẻẽẹêềếểễệ]': 'e',
    '[ìíỉĩị]': 'i',
    '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
    '[ùúủũụưừứửữự]': 'u',
    '[ỳýỷỹỵ]': 'y'
}


def convert_to_khongdau(text):
    """
    Convert from 'Tieng Viet co dau' thanh 'Tieng Viet khong dau'
    text: input string to be converted
    Return: string converted
    """
    output = text
    for regex, replace in patterns_kodau.items():
        output = re.sub(regex, replace, output)
        # deal with upper case
        output = re.sub(regex.upper(), replace.upper(), output)
    return output


def clearFormat(text):
    # chuyen thanh chu in thuong
    text = text.lower()
    # chuyen thanh tieng viet khong dau
    text = convert_to_khongdau(text)
    # loai bo space
    text = text.replace(' ', '')
    return text


def sqlEdit(sql=''):
    # for insert, update, delete command
    try:
        conn = mysql.connector.connect(
            host=hostDB,
            user=userDB,
            password=passDB,
            database=dataDB
        )
        conn.time_zone = "+07:00"
        curs = conn.cursor()
        curs.execute(sql)
        conn.commit()
        curs.close()
        conn.close()
        return("Success")
    except Exception as e:
        print("Error sqlEdit: ", sql)
        return("Fail")


def sqlselect(sql=str):
    try:
        conn = mysql.connector.connect(
            host=hostDB,
            user=userDB,
            password=passDB,
            database=dataDB
        )
        conn.time_zone = "+03:00"
        curs = conn.cursor()
        curs.execute(sql)
        rows = curs.fetchall()
        curs.close()
        conn.close()
        # print(rows)
        return rows
    except Exception as e:
        print("Error sqlselect: ", sql)
        return ''

# database có bảng giaovien(chat_id,chat_user,id_giaovien,ten_giaovien)


def write_user(chat_id, chat_user, permission):
    try:
        sql2 = "SELECT COUNT(*) FROM giaovien WHERE id_giaovien={};".format(chat_id)
        rows = sqlselect(sql2)
        if len(rows) > 0:
            if rows[0][0]:
                print("User has already existed !")
            else:
                sql1 = "INSERT INTO alert_list(user_id, user_name, permission, expiration) VALUES ({0},\'{1}\',\'{2}\',current_timestamp());".format(
                    chat_id, chat_user, permission
                )
                # print(sql1)
                sqlEdit(sql1)
    except Exception as e:
        print('Error write user: ', e)
        return ''


def parser_tkb_hnay(data_res):
    if not data_res:
        return ''

    tree = html.fromstring(data_res.text)
    tab_pane = tree.get_element_by_id(id='tab_12')
    if not tab_pane:
        return ''
    tkb_tuan = tab_pane.cssselect('tr')
    if not tkb_tuan:
        return ''
    # tr thứ nhất - tên các cột - không có nội dung lịch học- loai bỏ
    # các tr tiếp theo là các ngày có lịch dạy
    # mỗi tr (nội dung lịch) có 2 td
    # td 1 là thời gian
    # td 2 là lịch
    # [{'ngay':'thu 2','lich':string_lich},{}]
    lich_day = []
    lich_tuan_hoc_gv = []
    lich_mon_hoc_gv = []
    for i in range(len(tkb_tuan)):
        if i == 0:
            # loai bo tr1 - ten cot cua bang
            continue
        item_tkb = tkb_tuan[i].cssselect('td')
        if not item_tkb:
            print('Khong tim thay td')
            continue
        thoigian = html.tostring(
            item_tkb[0], method='text', encoding='unicode')
        str_1 = html.tostring(item_tkb[1], method='text', encoding='unicode')
        # print('string phan lich day', str_1)

        aa1 = str_1.find('sv)')+3
        aa = str_1.find('GV')
        bb = str_1.find('Phòng')
        cc = str_1.find('Tuần học')
        dd = str_1.find('Ngày học')

        tkb = f'{str_1[0:aa1]}\n{str_1[aa1:aa]}\n{str_1[bb:cc]}'
        # \n{str_1[cc:dd]}\n{str_1[dd:]} -- lich day
        #
        lich_day.append({'ngay_day': thoigian, 'lich_day': tkb})
        # lay mon hoc va ngay hoc mon do
        mon_hoc = str_1[aa1:aa]
        # xu ly trường hợp trong lịch học không có ngày học mà chỉ có tuần học
        if dd == -1:
            # chỉ lấy nội dung tuần học
            str_tuan_hoc = str_1[cc+9:]
            lich_tuan_hoc_gv.append(
                handle_lich_tuan_hoc(mon_hoc, str_tuan_hoc))
            # return lich_day, lich_mon_hoc
        else:
            # convert ngay len lop -> datetime
            lich_tuan_hoc_gv.append(
                handle_lich_tuan_hoc(mon_hoc, str_1[cc+9:dd]))
            lich_mon_hoc_gv.append(handle_lich_mon_hoc(mon_hoc, str_1[dd+9:]))
    return lich_day, lich_tuan_hoc_gv, lich_mon_hoc_gv


def today():
    today = datetime.now().date()
    return today


def this_week():
    this_week = datetime.now().strftime('%W')
    return this_week


def handle_lich_tuan_hoc(mon_hoc, str_tuan_hoc):
    str_tuan_hoc = str_tuan_hoc.replace(' ', '')
    ls = str_tuan_hoc.split('-')
    ls1 = []
    lich_tuan_hoc = []
    for i in ls:
        if i:
            ls1.append(i)
    lich_tuan_hoc.append({'mon_hoc': mon_hoc, 'tuan_hoc': ls1})
    # print('lich_tuan_hoc:', lich_tuan_hoc)
    return lich_tuan_hoc


def handle_lich_mon_hoc(mon_hoc, str_ngay_hoc):
    ngay_mon_hoc = str_ngay_hoc.split(',')
    # them year vao chuoi datetime
    # xac dinh year
    now = datetime.today()
    year = now.strftime('%Y')
    year = str(year)
    # them year
    ngay_mon_hoc_them_nam = []
    lich_mon_hoc = []
    for i in ngay_mon_hoc:
        i = i + '/' + year
        i = i.replace(' ', '')
        # print('str datetime:', f'"{i}"')
        i = datetime.strptime(i, '%d/%m/%Y').date()
        ngay_mon_hoc_them_nam.append(i)
    lich_mon_hoc.append(
        {'mon_hoc': mon_hoc, 'ngay_mon_hoc': ngay_mon_hoc_them_nam})
    return lich_mon_hoc
