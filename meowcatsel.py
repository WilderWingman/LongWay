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
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from threading import Thread

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

async def send_single_prompt(prompt):
    global sent_prompts_count  # Use the global variable

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off. Remove this line if you want to see the browser in action.

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.get("https://discord.com/channels/@me")  # Open Discord's login page

    # Login to Discord
    await asyncio.sleep(3)
    driver.find_element_by_name("email").send_keys("YOUR_DISCORD_EMAIL")
    driver.find_element_by_name("password").send_keys("YOUR_DISCORD_PASSWORD")
    driver.find_element_by_xpath("//button[contains(text(), 'Login')]").click()

    # Navigate to the server and channel where the bot is located
    await asyncio.sleep(5)  # Wait for the servers to load
    driver.find_element_by_xpath("//div[@aria-label='YOUR_SERVER_NAME, Server, Press to view server overview']").click()  # Replace YOUR_SERVER_NAME with the name of your server
    await asyncio.sleep(2)  # Wait for the channels to load
    driver.find_element_by_xpath("//div[contains(text(), 'YOUR_CHANNEL_NAME')]").click()  # Replace YOUR_CHANNEL_NAME with the name of your channel

    # Send the prompt
    await asyncio.sleep(2)  # Wait for the message input box to load
    message_input_box = driver.find_element_by_xpath("//div[@aria-label='Message #YOUR_CHANNEL_NAME']")  # Replace YOUR_CHANNEL_NAME with the name of your channel
    message_input_box.send_keys("/imagine")
    message_input_box.send_keys(Keys.RETURN)
    await asyncio.sleep(2)
    message_input_box.send_keys(prompt)
    message_input_box.send_keys(Keys.RETURN)

    driver.quit()  # Close the browser

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
        await send_single_prompt(prompt)

@bot.event
async def on_ready():
    print(f"{bot.user} is attempting to connect to Discord...")

@bot.event
async def on_ready():
    print(f"{bot.user} is attempting to connect to Discord...")

@bot.event
async def on_message(message):
    print("Received a message...")
    if message.author.bot:
        print("Processing bot message...")
        await process_midjourney_bot_message(message)
    elif message.content.startswith('!generate'):
        parts = int(message.content.split(":")[1])
        print(parts)
        if (parts) > 1:
            print("Queued multiple generations")
            try:
                num_generations = parts
                print(num_generations)
            except ValueError:
                pass

            Thread(target=generate_and_send_prompts, args=(num_generations,)).start()
            print('we made it here')
    else:
        print("Ignoring non-bot message...")

try:
    print("Starting bot...")
    bot.run(TOKEN)
    print("Bot has stopped.")
except Exception as e:
    print(f"Error running bot: {e}")
