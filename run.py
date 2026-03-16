# -*- coding: utf-8 -*-
import os
import sys

os.environ['TELEGRAM_BOT_TOKEN'] = '8721355269:AAFDShoTO5tNCzElFfjZo7Xv52nrnDL2qDg'
os.environ['POLYMARKET_PRIVATE_KEY'] = '0x01d32ef4ed44585faaeb2a71047a2a61d3708640b25c58b981e8d783606bd491'
os.environ['POLYMARKET_API_KEY'] = 'fbb433b7-4530-5f1e-0c3e-0689a03e15dc'
os.environ['ANTHROPIC_API_KEY'] = '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'
os.environ['OWNER_CHAT_ID'] = '8417313669'

sys.path.insert(0, os.path.dirname(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("bot", os.path.join(os.path.dirname(__file__), "bot.py"))
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)
bot.main()
