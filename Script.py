class script(object):
    #start_text
    START_TXT = """
𝐇𝐞𝐲 {},
😎 <b>{}</b>, 𝐘𝐨𝐮𝐫 𝐌𝐨𝐯𝐢𝐞 𝐁𝐮𝐝𝐝𝐲!
🌟 𝐓𝐞𝐥𝐥 𝐦𝐞 𝐲𝐨𝐮𝐫 𝐦𝐨𝐯𝐢𝐞 𝐰𝐢𝐬𝐡,
😋 𝐋𝐞𝐭'𝐬 𝐦𝐚𝐤𝐞 𝐦𝐨𝐯𝐢𝐞 𝐦𝐚𝐠𝐢𝐜!
🔮 𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐛𝐲 <a href=https://t.me/iPRIMEHUB>𝐏𝐫𝐢𝐦𝐞𝐇𝐮𝐛™</a>.
"""
    #status_text
    STATUS_TXT = """Total Files: <code>{}</code>
Total Users: <code>{}</code>
"""

    REQ_TEXT  = """#NewRequest
Bot - {}
Name - {} (<code>{}</code>)
Request - <b>{}</b>
"""

    LOG_TEXT_G = """#NewGroup
Group = {}(<code>{}</code>)
Total Members = <code>{}</code>
Added By - {}
"""

    LOG_TEXT_P = """#NewUser
ID - <code>{}</code>
Name - {}
"""

    #request_message
    REQM = """**To request for a movie please pass movie details along with** /request **command.**\n**Example**: <code>/request Avengers 2019</code>"""

    #request reply
    REQ_REPLY = """📍 **Your Request for** {} **has been submitted to the admins.**\n\n🚀 **Your Request Will Be Uploaded soon.**\n\n📌 **Please Note that Admins might be busy. So, this may take more time.**"""

    #remove ads
    REMADS_TEXT = """
<b>Free</b>\nAds & no direct links.\n\n<b>Premium</b>\nDirect files & no creepy ads, faster response time, no waiting time, web download and web streaming.\n\n<b>Plan Cost - ₹29/month & ₹145/6Month </b>\nPrices may increase in the future.
"""
    #confirm text
    CNFRM_TEXT = """
**UPI** -\n     <code>iPrimeHub@axl</code>\n          (tap2copy) \n\n**To Confirm Payment Process, Please Send Your Transaction Screenshot Or Transaction ID To** <a href=https://t.me/lemx4>L E M O N</a>\n\n**Admin delays may occur, request refund if plan activation fails.**
"""
    # Terms & Conditions
    TERMS = """
**By using our service, you agree to adhere to the following terms:

• The bot is provided on an "as is" basis, and we reserve the right to modify or discontinue its services without prior notice.
• While we make every effort to provide accurate movie information, we cannot guarantee the availability of all content.
• Advertisements displayed are independent of our control; any actions resulting from them are solely your responsibility.
• The bot collect user IDs for the purpose of providing updates and recording purchase history for premium services.
• We disclaim any responsibility for copyright infringement, and users are solely accountable for the utilization of our services.

By using our bot, you acknowledge that you have read, understood, and agreed these Terms.**
"""

    # removing blacklisted words
    BLACKLIST = ['tamilblaster', 'filmyzilla', 'streamershub', 'xyz', 'cine', 'www', 'http', 'https',
                'cloudsmoviesstore', 'moviez2you', 'bkp', 'cinema', 'filmy', 'flix',
                '4u', 'hub', 'movies', 'otthd', 'telegram', 'hoichoihok', '@', ']', '[',
                'filmy', 'films', 'cinema', 'join', 'club', 'apd', 'F-Press', 'GDTOT', 'GD',
                'backup', 'primeroom', 'theprofffesorr', 'premium', 'vip', '4wap', 'toonworld4all', 'mlwbd',
                'Telegram@alpacinodump', 'bollywood', "AllNewEnglishMovie", "7MovieRulz", "1TamilMV",
                'Bazar', '_Corner20', 'CornersOfficial', 'support', 'iMediaShare', 'Uᴘʟᴏᴀᴅᴇᴅ', 'Bʏ', 'PFM', 'alpacinodump'
                ]
