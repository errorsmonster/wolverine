class script(object):
    #start_text
    START_TXT = """𝐇𝐢 {},
😎 𝐈'𝐦 <b>{}</b>
👌 𝐈 𝐂𝐚𝐧 𝐒𝐞𝐚𝐫𝐜𝐡 𝐌𝐨𝐯𝐢𝐞𝐬 𝐅𝐨𝐫 𝐘𝐨𝐮
😋 𝐉𝐮𝐬𝐭 𝐒𝐞𝐧𝐝 𝐌𝐞 𝐀𝐧𝐲 𝐌𝐨𝐯𝐢𝐞 𝐍𝐚𝐦𝐞
🔮 𝐓𝐡𝐞𝐧 𝐒𝐭𝐚𝐧𝐝 𝐁𝐚𝐜𝐤 𝐀𝐧𝐝 𝐒𝐞𝐞 𝐓𝐡𝐞 𝐌𝐚𝐠𝐢𝐜 
🧑🏻‍💻 𝐌𝐚𝐢𝐧𝐭𝐚𝐢𝐧𝐞𝐝 𝐁𝐲 <a href=https://t.me/iPRIMEHUB>𝐏𝐫𝐢𝐦𝐞𝐇𝐮𝐛™</a>
"""
    #status_text
    STATUS_TXT = """Total Files: <code>{}</code>
Total Users: <code>{}</code>
Total Chats: <code>{}</code>
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
    REQ_REPLY = """📍 **Your Request for** <code>{}</code> **has been submitted to the admins.**\n\n🚀 **Your Request Will Be Uploaded soon.**\n\n📌 **Please Note that Admins might be busy. So, this may take more time.**"""

    #remove ads
    REMADS_TEXT = """
<b>Free</b>\nAds & no direct links\n\n<b>Premium</b>\nDirect files & no creepy ads, faster response time, no waiting time, premium access of our other services\n\n<b>Plan Cost - ₹19/month & ₹90/6-Month </b>\nPrices may increase in the future.\n<b>UPI</b> -\n    <code>iPrimeHub@axl</code>
"""
    #confirm text
    CNFRM_TEXT = """
**To Confirm Payment Process Please Send Your Transaction Screenshot Or Transaction ID To** <a href=https://t.me/lemx4>ｒｙｍｅ</a>\n\n**Admin delays may occur, request refund if plan activation fails.**
"""

    #paid group
    GROUP_PROMO = """Now You Can **Earn Money** By Adding This Bot In Your Group.\n\n**Requirements:**\n1. Your Group Must Have Minimum 500 Members.\n2. Your Group Must Be Active.\n3. Your Group Must Be Public. \n\n If You Are Interested Then Contact <a href=https://t.me/lemx4>ｒｙｍｅ</a>"""

    # removing blacklisted words
    BLACKLIST = ['www', 'tamilblaster', 'filmyzilla', 'streamershub', 'xyz', 'cine', 'link',
                'cloudsmoviesstore', 'moviez2you', 'bkp', 'cinema', 'filmy', 'bot', 'flix',
                '4u', 'hub', 'movies', 'otthd', 'telegram', 'hoichoihok',
                'mkv', 'mp4', '@', 'filmy', 'films', 'cinema', 'join', 'club', 'apd',
                'backup', 'primeroom', 'theprofffesorr', 'premium', 'vip', '4wap', 'toonworld4all', 'mlwbd'
                'Telegram@alpacinodump', 'bollywood', "AllNewEnglishMovie", "7MovieRulz", "1TamilMV",
                'Bazar', '_Corner20', 'CornersOfficial❣️', 'support', 'iMediaShare', '[', ']', '&', '✅',
                'Uᴘʟᴏᴀᴅᴇᴅ', 'Bʏ', ':', 'PFM']
