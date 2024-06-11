<h2>Personal Finance Telegram Bot</h2>
This project is a Telegram bot designed to help users manage their personal finances. It allows users to track their expenses, set monthly spending limits, categorize their transactions, view transaction history, and receive visual and CSV reports of their spending.

<div id="features">
    <h2>Features</h2>
    <ul>
        <li><strong>Track Expenses:</strong> Users can input each expense with details like amount, category, and a brief description.</li>
        <li><strong>Set Spending Limits:</strong> Users can define a monthly spending limit to help manage their budget.</li>
        <li><strong>Expense Categorization:</strong> Each expense can be categorized, and the bot features a categorization helper that groups similar categories.</li>
        <li><strong>View Transaction History:</strong> Users can view their past transactions, with support for pagination.</li>
        <li><strong>Spending Reports:</strong> The bot provides daily and monthly spending summaries, notifying users if they exceed their budget.</li>
        <li><strong>Data Export:</strong> Users can export a monthly report of their transactions in CSV format.</li>
        <li><strong>Visual Analytics:</strong> Users receive a pie chart visualizing their monthly spending by category.</li>
    </ul>
</div>

<div id="technologies-used">
    <h2>Technologies Used</h2>
    <ul>
        <li><strong>Python:</strong> The bot is written in Python, taking advantage of its extensive libraries and features.</li>
        <li><strong>aiogram:</strong> A Python library for building Telegram bots, used for handling updates and interactions with the Telegram Bot API.</li>
        <li><strong>Tortoise-ORM:</strong> An easy-to-use asyncio ORM (Object Relational Mapper) inspired by Django, used for async database interactions.</li>
        <li><strong>Pandas:</strong> A fast, powerful, flexible, and easy-to-use open-source data analysis and manipulation tool.</li>
        <li><strong>Matplotlib:</strong> A comprehensive library for creating static, animated, and interactive visualizations in Python.</li>
    </ul>
</div>

<div id="setup">
    <h2>Setup</h2>
    <p>Clone the repository:</p>
    <pre><code class="language-bash">git clone &lt;repository-url&gt;</code></pre>
    <p>Navigate to the repository folder and install dependencies:</p>
    <pre><code class="language-bash">cd &lt;repository-name&gt;
pip install -r requirements.txt</code></pre>
    <h3>Environment Variables:</h3>
    <p>Create a .env file in the root directory of the project.</p>
    <p>Add your Telegram bot token:</p>
    <pre><code class="language-makefile">BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN</code></pre>
    <h3>Start the Bot:</h3>
    <p>Run the bot script:</p>
    <pre><code class="language-bash">python bot.py</code></pre>
    <p>Or with Docker:</p>
    <pre><code class="language-bash">docker-compose build</code></pre> 
    <pre><code class="language-bash">docker-compose up</code></pre> 
    <p>The bot should now be running and responding to commands sent on Telegram.</p>
</div>

<div id="usage">
    <h2>Usage</h2>
    <p>Send /start to the bot in Telegram to begin.</p>
    <p>Follow the bot's prompts to add transactions, set a monthly limit, view reports, and more.</p>
</div>

<div id="contributing">
    <h2>Contributing</h2>
    <p>Contributions, issues, and feature requests are welcome. Feel free to check <a href="https://github.com/your_username/repo_name/issues">issues page</a> if you want to contribute.</p>
</div>

<div id="license">
    <h2>License</h2>
    <p>Distributed under the MIT License. See <a href="LICENSE">LICENSE</a> for more information.</p>
</div>

<div id="contact">
    <h2>Contact</h2>
    <p>Your Name - <a href="mailto:hallrizon@icloud.com">hallrizon@icloud.com</a></p>
    <p>Project Link: <a href="https://github.com/hallr1zon/finik_bot">https://github.com/hallr1zon/finik_bot</a></p>
</div>
