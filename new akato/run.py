import sys
import subtitle
import random
import open_ai.akato_ai
import Translate.MyTranslation
import VoiceRW.tts
import vts.vtube
import multiprocessing
import blivedm.sample
import asyncio
from VoiceRW.tts import Voicevox


sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

owner_name = "sugar"
audio_input = "input.wav"


# 异步处理问题并输出
def ask_out(question, message_data, question2, tts_data):
    while True:
        # 从问题队列获取问题
        text = question.get()

        # 想ai提问，获取回答
        message = open_ai.akato_ai.ask_ai(owner_name, text)
        print("[Akato]:", message)

        # voicevox的输入翻译
        # tts = Translate.MyTranslation.translate_GPT3(message, "Japanese")
        tts = Translate.MyTranslation.translate_google(message, "JA")
        print("[翻译器][日语]:", tts)

        question2.put(text)
        message_data.put(message)
        tts_data.put(tts)


# 语音阅读+动作触发
def voice_out(question, action_data, message_data, tts_data):
    vv = Voicevox()
    while True:
        # 从问题队列获取问题
        text = question.get()
        message = message_data.get()
        tts = tts_data.get()

        # 生成语音文件
        #VoiceRW.tts.voicevox_tts(tts, 46)

        # 生成字幕文本
        subtitle.generate_subtitle(text, message)

        # 阅读语音
        #VoiceRW.tts.read_wav()

        # 生成+阅读语音
        vv.speak(text = tts, speaker = 46)

        # 概率性触发动作
        sp = random.randint(1,100)
        if sp > 0 and sp <= 2:
            action_data.value = 4
        elif sp > 2 and sp <= 10:
            action_data.value = 3
        elif sp > 10 and sp <= 40:
            action_data.value = 1
        elif sp > 40 and sp <= 100:
            action_data.value = 2

        # 清空字幕文本
        with open("output.txt", "w") as f:
            f.truncate(0)
        with open("chat.txt", "w") as f:
            f.truncate(0)


def vtube_sport(shared_data):
    vts.vtube.vtube_worker(shared_data)


def listen():
    VoiceRW.tts.audio_listen()
    text = open_ai.akato_ai.transcribe_audio(audio_input)
    print("[question]:" + text)
    return text


def BliveDM(question):
    asyncio.run(blivedm.sample.main(question))


if __name__ == '__main__':
    # 创建队列
    question = multiprocessing.Queue(maxsize=0)
    question2 = multiprocessing.Queue(maxsize=0)
    message = multiprocessing.Queue(maxsize=0)
    tts_data = multiprocessing.Queue(maxsize=0)
    action_data = multiprocessing.Value('i', 0)

    # 创建进程并启动
    p1 = multiprocessing.Process(target=ask_out, args=(question, message, question2, tts_data))
    p2 = multiprocessing.Process(target=vtube_sport, args=(action_data,))
    p3 = multiprocessing.Process(target=BliveDM, args=(question, ))
    p4 = multiprocessing.Process(target=voice_out, args=(question2, action_data, message, tts_data))
    p1.start()
    p2.start()
    p3.start()
    p4.start()

    while True:
        q = listen()
        # 向队列1放入初始数据
        question.put(q)

    # 主进程等待子进程结束
    p1.join()
    p2.join()
    p3.join()
    p4.join()
