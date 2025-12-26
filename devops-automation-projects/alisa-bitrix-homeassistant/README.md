# Alisa + Bitrix24 + Home Assistant Integration

## 🧠 Overview

A webhook service that receives Bitrix24 events and sends voice notifications
to Yandex Smart Speakers and other TTS endpoints via Home Assistant.

## 📌 Features

- Listens for Bitrix24 POST webhooks
- Sends TTS (text-to-speech) messages to smart devices
- Handles errors and retries
- Easy to configure

## 🛠 Setup

1. Copy `config.example.py` → `config.py`
2. Fill in your Home Assistant token & URL
3. Install dependencies:
