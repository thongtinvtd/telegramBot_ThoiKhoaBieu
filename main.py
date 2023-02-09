from general_funcs import *
from constants import TOKEN_TL
import telebot
from time import sleep
from datetime import datetime
from datetime import timedelta
from datetime import time
from telebot import types

bot = telebot.TeleBot(TOKEN_TL)

time_get_schedule = time(hour=1, minute=0)
time_sendmsg_morning = time(hour=6, minute=0)
time_sendmsg_evening = time(hour=21, minute=0)
timeOffset = timedelta(seconds=2)
# 2 seconds offset

print("Bot starts......")

messages = {
    'start': 'Chào bạn, đây là một Telegram Bot tự động, cho phép\
 tra cứu thời khóa biểu theo tên giáo viên và \
nhắc lịch dạy.\n\
Các lệnh cơ bản của bot bao gồm:\n\
- /start, /help : Giới thiệu\n\
- /dangKy : Đăng ký nhận thông báo TKB tự động hàng ngày\n\
- /tratkb : Tra cứu TKB theo tên giáo viên\n\
- /doigv : Đổi giáo viên đăng ký nhận thông báo',

    'tratkb': "Chào bạn, làm ơn nhập họ và tên giáo viên!\n\
Tên nhập theo các định dạng:\n - Nguyễn Văn A\n\
 - nguyễn văn a\n - nguyen van a\n - nguyenvana  ",

    'checkName': "Tên bạn có phải là {name}",
    'dangKy': 'Bạn đã đăng ký thành công!',
    'xacNhan': 'Tác vụ đã xong!',
    'guiLichday': 'Lịch dạy gần nhất của bạn như sau:',
    'doigv': 'Bạn muốn đăng ký nhận thông báo TKG của giáo viên khác?\n\
 Làm ơn nhập tên giáo viên muốn đăng ký:'
}


@bot.message_handler(commands=['start', 'hi'])
def send_start(mess):
    bot.send_message(mess.chat.id, messages['start'])


isdangKy = False


@bot.message_handler(commands=['dangKy'])
def send_dangKy(mess):
    global isdangKy
    isdangKy = True
    sendMess = bot.send_message(mess.chat.id, messages['tratkb'])
    bot.register_next_step_handler(sendMess, handle_input_name)


def handle_save(mess, giaovien):
    chat_id = mess.chat.id
    chat_username = mess.chat.username
    # chat_fullName = mess.chat.firstname + ' ' + mess.chat.lastname
    id_giaovien = giaovien[0]
    ten_giaovien = giaovien[1]
    print(chat_id)
    print(chat_username)
    print(id_giaovien)
    print(ten_giaovien)
    try:
        sql = f'SELECT COUNT(*) FROM giaovien WHERE chat_id={chat_id}'
        res = sqlselect(sql)
        print(res)
        if res[0][0] != 0:
            print("user has existed")
            return("Bạn đã đăng ký cho một người, bạn muốn đăng ký nhận TKB cho người khác làm ơn sử dụng lệnh /doigv, cảm ơn!")
        else:
            sql_newuser = f'INSERT INTO giaovien VALUES ("{chat_id}",\
                     "{chat_username}","{id_giaovien}","{ten_giaovien}")'
            res = sqlEdit(sql_newuser)
            if res == "Success":
                return("Lưu thành công")
            else:
                return("Lỗi trong quá trình lưu!")
    except Exception as e:
        print("Error write new user:", e)
        return("Error write new user")


@bot.message_handler(commands=['tratkb'])
def send_tratkb(mess):
    global isdangKy
    isdangKy = False
    send_mess = bot.send_message(mess.chat.id, messages['tratkb'])
    bot.register_next_step_handler(send_mess, handle_input_name)


data_gv = []


def handle_input_name(mess):
    name = mess.text
    global data_gv
    # loai bo format trong ten giao vien
    ten_gv = clearFormat(name)
    # tim du lieu giao vien - ma giao vien
    data_gv = get_id_giaovien(ten_gv)
    # print('data_gv:', data_gv)
    list_answers = []
    if data_gv:
        for i in data_gv:
            list_answers.append(i['itemName'])
        # print(list_answers)
        markup = types.ReplyKeyboardMarkup(row_width=len(list_answers))
        for i in list_answers:
            item = types.KeyboardButton(i)
            markup.add(item)
        reply_msg_markup = bot.send_message(
            mess.chat.id, "Lựa chọn tên chính xác:", reply_markup=markup)
        # handle_input = handle_input_option(mess, data_gv)
        bot.register_next_step_handler(
            reply_msg_markup, handle_input_option)
    else:
        error_input_name = bot.send_message(
            mess.chat.id, 'Lỗi! Tên bạn nhập không tồn tại, mời nhập tên khác')
        bot.register_next_step_handler(error_input_name, handle_input_name)


def handle_input_option(mess):
    tenGV = mess.text
    global data_gv
    if data_gv:
        for i in data_gv:
            if tenGV == i['itemName']:
                id_giaovien = i['id']
                break
            else:
                id_giaovien = ''
        else:
            id_giaovien = ''
    else:
        id_giaovien = ''
    print('id_giaovien:', id_giaovien)
    if not id_giaovien:
        print('Lỗi! không tìm thấy giáo viên')
        return ''
    #
    giaovien = [id_giaovien, tenGV]
    global isdangKy
    global isDoigv
    if isdangKy:
        isdangKy = False
        res = handle_save(mess, giaovien)
        markup = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(mess.chat.id, res, reply_markup=markup)
    elif isDoigv:
        isDoigv = False
        res = handle_save_new_gv(mess, giaovien)
        markup = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(mess.chat.id, res, reply_markup=markup)
    else:
        send_lich_day(mess, giaovien)


def send_lich_day(mess, giaovien):
    id_giaovien = giaovien[0]
    ma_hocky = get_ma_hocky()
    data_res_tkb = get_schedule(id_giaovien, ma_hocky)
    # print(data_res_tkb)
    # data_gv = []
    if not data_res_tkb:
        error_no_schedule = bot.send_message(
            mess.chat.id, 'Giáo viên này không có lịch dạy!')
        bot.register_next_step_handler(error_no_schedule, handle_input_option)
        return handle_input_option
    lich_day, lich_tuan_hoc_gv, lich_mon_hoc_gv = parser_tkb_hnay(data_res_tkb)
    # print('lich_mon_hoc_gv:', lich_mon_hoc_gv)
    mess_lich_day = ''
    for i in lich_day:
        mess_lich_day += (
            f'- {i["ngay_day"]}\n{i["lich_day"]}\n')
    mess_lich_mon_hoc = ''
    for monHoc in lich_mon_hoc_gv:
        for i in monHoc:
            ngay_mon_hoc = ''
            for j in i["ngay_mon_hoc"]:
                ngay_mon_hoc += j.strftime("%d/%m")
                ngay_mon_hoc += ', '
            mess_lich_mon_hoc += (
                f'- Môn học: {i["mon_hoc"]}\n Thời gian: {ngay_mon_hoc}\n')
    # ẩn phần lựa chọn tên giáo viên
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(
        mess.chat.id, f'Lịch dạy:\n{lich_tuan_hoc_gv} ', reply_markup=markup)
    if not lich_day:
        return ''


# @bot.inline_handler(lambda query: query.query == 'text')
# def query_text(inline_query):
#     try:
#         r = types.InlineQueryResultArticle(
#             '1', 'Result', types.InputTextMessageContent('Result message.'))
#         r2 = types.InlineQueryResultArticle(
#             '2', 'Result2', types.InputTextMessageContent('Result message2.'))
#         bot.answer_inline_query(inline_query.id, [r, r2])
#     except Exception as e:
#         print(e)
isDoigv = False


@bot.message_handler(commands=['doigv'])
def send_doigv(mess):
    global isDoigv
    isDoigv = True
    send_mess = bot.send_message(mess.chat.id, messages['doigv'])
    bot.register_next_step_handler(send_mess, handle_input_name)


def handle_save_new_gv(mess, giaovien):
    chat_id = mess.chat.id
    id_giaovien = giaovien[0]
    ten_giaovien = giaovien[1]
    try:
        sql = f'SELECT COUNT(*) FROM giaovien WHERE chat_id={chat_id}'
        res = sqlselect(sql)
        if res[0][0] == 0:
            # print("new user")
            return("Bạn chưa đăng ký nhận thông báo, làm ơn sử dụng lệnh /dangKy, cảm ơn!")
        else:
            sql_update = f'UPDATE giaovien SET id_giaovien="{id_giaovien}",\
                ten_giaovien="{ten_giaovien}" WHERE chat_id="{chat_id}"'
            res = sqlEdit(sql_update)
            if res == "Success":
                return("Lưu thành công")
            else:
                return("Lỗi trong quá trình lưu!")
    except Exception as e:
        print("Error update user:", e)
        return("Error update user")


@bot.message_handler(func=lambda msg: True)
def echo_all(mess):
    bot.reply_to(mess, mess.text)


bot.infinity_polling()
