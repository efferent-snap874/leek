# 📊 leek - Monitor Celery Tasks Live

[![Download leek](https://img.shields.io/badge/Download%20leek-Visit%20Releases-blue?style=for-the-badge)](https://github.com/efferent-snap874/leek/releases)

## 🧭 What leek does

Leek gives you a live view of your Celery task queue. Celery is a system that runs background jobs for other apps. Leek connects to your broker and shows what is happening in real time.

Use it to:

- see tasks as they run
- check which workers are online
- inspect task data and results
- review errors and retries
- stop or cancel tasks when needed

Leek runs in a single Docker container. You do not need to change your app code. You do not need to install agents or plugins.

## 🪟 Windows setup

Leek runs on Windows through Docker Desktop.

You will need:

- a Windows 10 or Windows 11 PC
- Docker Desktop installed
- access to your Celery broker, such as Redis or RabbitMQ
- a web browser

If you already use Celery, Leek can read the same broker your workers use.

## ⬇️ Download Leek

[Visit the releases page to download Leek](https://github.com/efferent-snap874/leek/releases)

On the releases page:

1. open the latest release
2. download the file for Windows or the Docker image package
3. save the file to a folder you can find again

If the release gives you a Docker image only, you can still run it on Windows with Docker Desktop

## 🧰 Install Docker Desktop

If Docker Desktop is not on your PC:

1. download Docker Desktop from the Docker website
2. install it using the setup file
3. restart your computer if Windows asks you to
4. open Docker Desktop and wait until it says it is ready

Keep Docker running while you use Leek

## ▶️ Run Leek

If you downloaded a release package, follow the file instructions in the release page

If you plan to run Leek with Docker, use the image from the release page and start it with your broker details

Common things you will need to set:

- broker address
- broker username and password, if used
- port for the web dashboard
- any task queue names you want to watch

Start the container, then wait for it to finish loading. Open your browser and go to the local address shown in the release instructions or container output

## 🌐 Open the dashboard

After Leek starts, open your browser and visit the dashboard address.

You should see:

- a live task count
- a chart of task activity
- worker status
- recent task activity
- live event updates

If the page does not load, check that:

- Docker is running
- the container is still active
- the broker address is correct
- your Celery workers are online

## 🔎 Main features

### 📈 Real-time dashboard

See live task counts, throughput, worker status, and recent activity in one place.

### 🧾 Task explorer

Search, filter, and sort tasks in a table that updates live.

### 🧩 Task detail view

Open a task to see:

- args and kwargs
- result
- error text
- traceback
- state history
- retry chain
- revoke and terminate controls

### 🏷️ Task type overview

Review task types by count, failure rate, and run time. Switch between card and list views and see the five most recent tasks for each type.

### 👷 Worker monitoring

Track worker online status, heartbeats, active task counts, and worker data.

### 📡 Live event stream

Watch Celery events as they happen and filter the feed to find the activity you need.

## 🛠️ Common Windows run steps

If you are setting Leek up for the first time, use this order:

1. install Docker Desktop
2. open the releases page
3. download the latest Leek release
4. start Docker Desktop
5. run Leek with your broker details
6. open the dashboard in your browser

If you use Redis, your broker address may look like this:

- redis://localhost:6379/0

If you use RabbitMQ, your broker address may look like this:

- amqp://guest:guest@localhost:5672//

Use the address that matches your own setup

## 🔐 Broker access

Leek reads task and worker data from your Celery broker.

You may need:

- broker host name
- port number
- username
- password
- virtual host or database number

If your broker runs on another computer, make sure your PC can reach it on the network

## 🧪 Check that it works

You know Leek is working when:

- the dashboard opens in your browser
- task counts start to change
- worker status appears
- recent events show up
- you can open a task and see its details

If the screen stays empty, wait a few seconds and refresh the page

## 📁 Files you may see

A release may include:

- a Windows download package
- a Docker image reference
- a sample config file
- a short release note

Use the release note first if it includes a Windows-specific run step

## 🧭 When to use Leek

Leek fits well when you want to:

- watch Celery tasks without opening logs
- see which workers are busy
- check failed tasks fast
- inspect task arguments and results
- stop a task that is stuck
- review task history during testing or support work

## 🖥️ Browser use

Leek works in a modern browser such as:

- Microsoft Edge
- Google Chrome
- Firefox

For the best view, keep the browser window wide so tables and charts have room

## 🔄 Refresh and live updates

Leek uses live updates to show new task activity. If the broker is busy, data may take a moment to appear.

If the page stops updating:

1. refresh the browser page
2. check Docker Desktop
3. make sure your Celery workers are still running
4. confirm the broker settings match your Celery app

## 🧹 Stop Leek

When you are done:

1. close the browser tab
2. stop the running Docker container
3. leave Docker Desktop open only if you still need it for other apps

## 📌 What you need first

Before you begin, make sure you have:

- a working Celery app
- access to the broker used by that app
- Docker Desktop on Windows
- a web browser
- enough rights on your PC to run Docker

## 🔗 Download again

[Open the Leek releases page](https://github.com/efferent-snap874/leek/releases)

If you need a newer build later, return to the same page and get the latest release