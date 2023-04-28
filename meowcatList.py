import os
import random
import time
import discord
import aiohttp
import cv2
import numpy as np
from discord.ext import commands
from PIL import Image
import requests
import asyncio
import pyautogui as pg
from collections import deque
import logging
import csv

TOKEN = 'MTA5ODgwMTA1NDYxNjkzMjUwMw.GYxGUJ.1ALaaiPLv0SKwYDBQHAx8Jb0WOmBgdDlJ1btN4'


intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

TRIGGER_MESSAGE = "(waiting to start)"

num_generations = 1

output_directory = "C:\meowcat69000"

# Initialize a deque for the prompt queue
prompt_queue = deque()
waiting_for_trigger = asyncio.Event()

# Add counters for sent prompts and processed images
sent_prompts_count = 0
processed_images_count = 0

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

def read_prompt_data(file_name="C:\meowcat69000\prompt_data.csv"):
    data = []
    with open(file_name, "r") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data.append(row)
    return data

def prompt_generator(prompt_data):
    while True:
        row = prompt_data[sent_prompts_count % len(prompt_data)]
        yield row[0]

prompt_data = read_prompt_data()
prompt_gen = prompt_generator(prompt_data)

def upscale_image(image_data, scale_factor=2):
    input_image = cv2.imdecode(np.asarray(bytearray(image_data), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    height, width = input_image.shape[:2]
    new_width, new_height = width * scale_factor, height * scale_factor
    upscaled_image = cv2.resize(input_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    return upscaled_image

def save_prompts_to_file(prompts):
    with open('prompts.txt', 'w') as prompt_file:
        for prompt in prompts:
            prompt_file.write(prompt + '\n')

def save_image(image_data, output_filename):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_path = os.path.join(output_directory, output_filename)
    cv2.imwrite(output_path, image_data)
    print(f"Saved image: {output_path}")


async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            image_data = await response.read()
    return image_data

async def upscale_and_save_image(image_data, output_filename):
    upscaled_image_data = upscale_image(image_data)
    output_path = os.path.join(output_directory, output_filename)
    print(f"Output path: {output_path}")
    save_image(upscaled_image_data, output_path)
    print(f"Upscaled and saved image: {output_path}")

def should_send_next_prompt(message_content):
    return TRIGGER_MESSAGE.lower() in message_content.lower()

async def process_midjourney_bot_message(message):
    content = message.content.lower()
    if "%" in content or "waiting to start" in content or "Upscaled" in content:
        print('message not valid')
        return

    if not message.attachments:
        print('no attachment detected')
        return

    attachment = message.attachments[0]
    global processed_images_count  # Use the global variable
    if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        print('attachment found')
        image_data = await download_image(attachment.url)
        output_filename = f"Fourpack_{attachment.filename}"
        await upscale_and_save_image(image_data, output_filename)
        print(processed_images_count)
        processed_images_count += 1  # Increment the processed images count
        print(processed_images_count)
    elif "open on website for full quality" in content:  # Add this condition
        print("Found full quality image message")
        processed_images_count += 1  # Increment the processed images count
        print(processed_images_count)

async def send_single_prompt(message):
    global sent_prompts_count  # Use the global variable
    if not prompt_queue:
        print("No prompts in the queue.")
        return

    prompt = next(prompt_gen)
    prompt_queue.append(prompt)
    save_prompts_to_file(prompt_queue)

    await message.channel.send("Automation will start in 3 seconds...")
    await asyncio.sleep(random.uniform(3,4))
    pg.write('/imagine')
    await asyncio.sleep(random.uniform(4,6))
    pg.press('tab')
    pg.write(prompt)
    await asyncio.sleep(random.uniform(3,5))
    pg.press('enter')
    print(sent_prompts_count)
    sent_prompts_count += 1  # Increment the sent prompts count
    print(sent_prompts_count)
    await asyncio.sleep(random.uniform(6,12))

async def generate_and_send_prompts(message, num_generations):
    global sent_prompts_count, processed_images_count  # Use the global variables
    print('generate_and_send_prompts')
    print(num_generations)
    for _ in range(0, num_generations):
        # Check to ensure the bot sends the next prompt only if the difference between sent_prompts_count and processed_images_count is less than 7
        while sent_prompts_count - processed_images_count >= 7:
            await asyncio.sleep(random.uniform(6,10))
            print(processed_images_count)

        print('Sending prompt')
        prompt = next(prompt_gen)  # Use the prompt_gen instance
        prompt_queue.append(prompt)
        save_prompts_to_file(prompt_queue)
        await send_single_prompt(message)
        print('Print sent')
        await asyncio.sleep(random.uniform(5,9))

@bot.event
async def on_ready():
    print(f"{bot.user} is attempting to connect to Discord...")

@bot.event
async def on_message(message):
    print("Received a message...")
    if message.author.bot:
        print("Processing bot message...")
        await process_midjourney_bot_message(message)
    else:
        print("Ignoring non-bot message...")
    
    if message.content.startswith('!generate'):
        parts = int(message.content.split(":")[1])
        print(parts)
        if (parts) > 1:
            print("Queued multiple generations")
            try:
                num_generations = parts
                print(num_generations)
            except ValueError:
                pass

            await generate_and_send_prompts(message, num_generations)
            print('we made it here')

    else:
        print("Trigger is not set.")

try:
    print("Starting bot...")
    bot.run(TOKEN)
    print("Bot has stopped.")
except Exception as e:
    print(f"Error running bot: {e}")

