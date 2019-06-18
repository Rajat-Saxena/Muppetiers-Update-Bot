import os
import praw  # Python Reddit API Wrapper
import datetime
import pytz
import pymysql.cursors


def get_last_comment(connection):
    try:
        with connection.cursor() as cursor:
            # Read a single record
            sql = "SELECT `comment_id`, `created_utc` FROM `muppet_bot_tbl`"
            cursor.execute(sql)
            result = cursor.fetchone()
            comment_id = result['comment_id']
            created_utc = result['created_utc']
            print('Last comment id: ' + comment_id + ' and last comment timestamp: ' + str(created_utc))

    except Exception as e:
        print('ERROR while reading last comment')
        print(e)

    return comment_id, created_utc


def save_last_comment(connection, comment):
    try:
        with connection.cursor() as cursor:
            # Create a new record
            sql = "UPDATE `muppet_bot_tbl` SET `comment_id` = '" + str(comment.id) + "', `created_utc` = '" + str(
                comment.created_utc) + "'"
            cursor.execute(sql)

        connection.commit()
		
    except Exception as e:
        print('ERROR while saving last comment into database')
        print(e)


def check_condition(comment):
    tokens = comment.body.split()
    if len(tokens) < 2:
        return False

    if "!MuppetiersUpdateBot" in tokens:
        count = tokens[1]
        if count.isdigit():
            return True


def bot_action(comment, comment_limit, reddit, connection):
    muppets = ['muppetiers']
    response = ''
    bst = pytz.timezone('Europe/London')
    for muppet in muppets:
        response += '\n#Latest comments by ' + muppet + '\n'
        i = 1
        for c in reddit.redditor(muppet).comments.new(limit=comment_limit):
            if c.subreddit.display_name == 'reddevils' and 'Transfer Muppets Thread' in c.link_title:
                utc_posted_time = datetime.datetime.utcfromtimestamp(c.created_utc).astimezone(pytz.utc)
                dttm_bst = utc_posted_time.astimezone(bst)
                response += '\n##Comment ' + str(i) + '\n'

                comm = str(c.body).replace('*', '').replace('#', '').replace('u/', 'u\\')
                response += comm + '\n'
                response += '\n^(Posted on ' + str((dttm_bst).strftime("%d-%m-%Y %H:%M")) + ' BST) '
                response += '\n[^(link)](' + str(c.permalink) + ')'
                i = i + 1

                save_last_comment(connection, comment)

    response += '\n\n---\n' \
                + '^(Beep boop. I am a bot. If you have any feedback, contact my )' \
                + '[^(Creator.)](https://www.reddit.com/message/compose/?to=rajatsaxena&subject=Muppet-Bot)'
    #print(response)
    comment.reply(response)


print('Starting app at ' + str(datetime.datetime.now()))
praw_client_id = os.environ['praw_client_id']
praw_client_secret = os.environ['praw_client_secret']
praw_password = os.environ['praw_password']
praw_username = os.environ['praw_username']
print('Env vars set')

# Connect to database
print('Establishing connection to database')
connection = pymysql.connect(host=os.environ['jawsdb_host'],
                             user=os.environ['jawsdb_user'],
                             password=os.environ['jawsdb_password'],
                             db=os.environ['jawsdb_db'],
                             port=3306,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

reddit = praw.Reddit(client_id=praw_client_id, client_secret=praw_client_secret, password=praw_password,
               user_agent='web:com.muppetiers-update-bot:v0.1 (by /u/rajatsaxena)',
               username=praw_username)
print('Logged on to Reddit')

print('Starting comments stream')
subreddit = reddit.subreddit('reddevils')
for comment in subreddit.stream.comments():
    if check_condition(comment):
        last_comment_id, last_created_utc = get_last_comment(connection)
        if comment.created_utc > last_created_utc:
            print('Responding to comment_id: ' + comment.id + ' created: ' + str(comment.created_utc) + ' with body: ' + comment.body)
            bot_action(comment, int(comment.body.split()[1]), reddit, connection)
