

import asyncio
import sqlite3

from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async, run_js

import json


MAX_MESSAGES_CNT = 10 ** 4

chat_msgs = []  # The chat message history. The item is (name, message content)
online_users = set()

# Create a SQLite database to store the chat messages
conn = sqlite3.connect("chat_room.db")
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
    name text,
    message text
)""")
conn.commit()

# save in json

cursor.execute("SELECT name, message FROM chat_messages")
data = cursor.fetchall()

with open('chat_data.json', 'w') as f:
    json.dump(data, f)

# save date in sql

with open('dump.sql', 'w') as f:
    for line in conn.iterdump():
        f.write('%s\n' % line)
#


def t(eng, chinese):
    """return English or Chinese text according to the user's browser language"""
    return chinese if 'zh' in session_info.user_language else eng


async def refresh_msg(my_name):
    """send new message to current session"""
    global chat_msgs
    last_idx = len(chat_msgs)
    while True:
        await asyncio.sleep(0.5)
        for m in chat_msgs[last_idx:]:
            if m[0] != my_name:  # only refresh message that not sent by current user
                put_markdown('`%s`: %s' % m, sanitize=True, scope='msg-box')

        # remove expired message
        if len(chat_msgs) > MAX_MESSAGES_CNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)


async def main():
    """chat room

    You can chat with everyone currently online.
    """
    global chat_msgs

    put_markdown(
        t("#### Welcome to the chat room, you can chat with all the people currently online. You can open this page in multiple tabs of your browser to simulate a multi-user environment.The source code is [here](https://nowayno.info)", "## PyWebIO聊天室\n欢迎来到聊天室，你可以和当前所有在线的人聊天。你可以在浏览器的多个标签页中打开本页面来测试聊天效果。本应用使用不到90行代码实现，源代码[链接](https://github.com/wang0618/PyWebIO/blob/dev/demos/chat_room.py)"))

    put_scrollable(put_scope('msg-box'), height=300, keep_bottom=True)
    nickname = await input(t("Your nickname", "请输入你的昵称"), required=True, validate=lambda n: t('This name is already been used', '昵称已被使用') if n in online_users or n == '📢' else None)

    online_users.add(nickname)
    chat_msgs.append(('📢', '`%s` joins the room. %s users currently online' % (
        nickname, len(online_users))))
    put_markdown('`📢`: `%s` join the room. %s users currently online' % (
        nickname, len(online_users)), sanitize=True, scope='msg-box')

    # Query all the messages from the SQLite database
    cursor.execute("SELECT name, message FROM chat_messages")
    for name, message in cursor.fetchall():
        chat_msgs.append((name, message))
        put_markdown('`%s`: %s' % (name, message),
                     sanitize=True, scope='msg-box')

    @defer_call
    def on_close():
        online_users.remove(nickname)
        chat_msgs.append(('📢', '`%s` leaves the room. %s users currently online' % (
            nickname, len(online_users))))

    refresh_task = run_async(refresh_msg(nickname))

    while True:
        data = await input_group(t('Send message', '发送消息'), [
            input(name='msg', help_text=t(
                'Message content supports inline Markdown syntax', '消息内容支持行内Markdown语法')),
            actions(name='cmd', buttons=[t('Send', '发送'), t('Multiline Input', '多行输入'), {
                    'label': t('Exit', '退出'), 'type': 'cancel'}])
        ], validate=lambda d: ('msg', 'Message content cannot be empty') if d['cmd'] == t('Send', '发送') and not d['msg'] else None)
        if data is None:
            break
        if data['cmd'] == t('Multiline Input', '多行输入'):
            data['msg'] = '\n' + await textarea('Message content', help_text=t('Message content supports Markdown syntax', '消息内容支持Markdown语法'))
        put_markdown('`%s`: %s' %
                     (nickname, data['msg']), sanitize=True, scope='msg-box')
        chat_msgs.append((nickname, data['msg']))
        # Store the message to the SQLite database
        cursor.execute("INSERT INTO chat_messages VALUES (?, ?)",
                       (nickname, data['msg']))
        conn.commit()

    refresh_task.close()
    toast("You have left the chat room")

    put_buttons(['Reset'], onclick=lambda btn: run_js(
        'window.location.reload()'))


if __name__ == '__main__':
    start_server(main, debug=False, port=2000)
