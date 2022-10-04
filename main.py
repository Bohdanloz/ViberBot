from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest
from viberbot.api.event_type import EventType

import time
import logging
import sched
import threading
import os
import datetime as dt
import json

from bs4 import BeautifulSoup
import urllib.request, urllib.error, urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='Botchat',
    avatar='data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAoHCBAQDw8PDxEREA8QDxEQDw8PEhERDxAPGBQZGRgUGRgcIS4lHB4sLRgYJjgnODExQzU1GiQ7QDs0QC40NTYBDAwMEA8QHxIRHj8rJSY/NjQ0PzE4NT82MT09NDE0OjQ0PzQ4NDg0NjY/NTQ7ODY0PTQxNDE0PzQ/PTU6NDQ0Mf/AABEIAKkBKwMBIgACEQEDEQH/xAAbAAEAAwEBAQEAAAAAAAAAAAAAAQYHBQQDAv/EAEkQAAICAQICBQcGCggGAwAAAAECAAMRBBIFIQYTMUFRFSJUYYGT0gcUMnGR0SM0NVJyc3SUsrMWQlNiobHB0yWkwuHw8TOCov/EABkBAQADAQEAAAAAAAAAAAAAAAABAgMEBf/EACgRAQABAwIGAgEFAAAAAAAAAAABAgMRE1ESFCExMmEEQaEFIoGR4f/aAAwDAQACEQMRAD8A2WIiAiIgIiICIiAiIgIzEQEYiICIiAiIgZ9xjpm41FtdTmqumx6gUqS17LEJVyxZgFQEEAAZOM5GcSw9E+OnXUuzhRdTZ1dhQMqWeaGFig81Bz2EnBBGSME0LpvwC7Tap7dPstq1Bu1PVk7bKmBDWczyYFnyO/ziMcsy9dDeAtoNOy2utl9riy0pnq180AImeZUY7T2kk8uwd96PjaEcHl0/0WOIicARiIgIiIDMREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBEStcasY6pk666uuvSJbtpfblzY49vYPsgWWJRW1pHZdrD9d4X/Qz0UUa21Osr+dbSMqW1QBYdxUHH+OIHz6S279Y69q1VJXjwZsu32hq/slk6PXF9FpmJywrWtz4unmMftUyiX6bdY7O162FvwoaywNuCgc+fgF9mO6e3hem1LfgdM9wVSWb8M61oWJOSTntOTgZgaBEo2sr12nI6624BjgOlzvWWxnbnkQeXeB6szicU4rq62TZqrwrKeW8nzgef+YgapErnQfV23aRnudrGF7qGc5baApAz7TLHAREQEREBERAREQEREBERASZEQESZEBERARJiBEREBERARJiBEREDl9IbzXp9+XUdbSrGs7X2tYoOD3dsqV2qVr79jWMDptOn4Vy7Z621jgknl5ssfTBbDobOqRrHFlDBERnYgWqT5qjJ7zKNo9OzoLHa1LH3K65KFdruAm0jljzhiB69Q5VHYJ1hUbur/tAOZT24I9soPRfp1xe3i2mLaiy4ajUV12aY5NBrZwGCp2JgEncPDnnnL1W7Iwrc5DH8HYced37W/vf5j15k6bSV1WvfTWtVzgh7awEsYHt88cxn1QO30kZW1b7cErVWj47N+XOD68MvsImXdPOkOv01yabT226WnHXB9PY9bX2HkWZlIJwFVcerPfL6Bjs8SfrJOSfrnx1OkrtCi1EcK25d6htreIz2GB7ej3F79T0f09mty2otcJWzgB7gl2Vsx6gpOe/bnvnG42PMQ+DkfaP+06Tt/Xdidq43u7NtQc8ZY8l9XZK/xTVG1ggDIiHIJGHckcjz7F58vGB2ejesVNLqAz6hWW2wr1TsiD8EhHIMOeczSdIxaqtick1oSfElRkzFdK16kpQtlpcOWqRHsLHZjdtUZ7hNq0gIqrBGCK1BB7Qdo5QPtEmRAREQERJgRESYEREQESZEBEmIEREQEREBERASZEQEQIgIiICIiBMoNulcruVWb8Pq1bapOCNVb4fX/hL7KvxSjS1WMldVll7brnC6m+mmsOxJZ2DYTcd2AASTnl3wOBdp9ylXQ7T2ggj257j655vmafnW/vGo+OdCnimiWzq9QrKNwUvRrdZYEY/nq20gcxzGe3sxzn14/Zw1dO/zewWXP5iEavUNsLcus+kc7e3Hqgcr5mn51v7xqPjj5mn51v7xqPjnO3L+en71q5DkEECxASCAfnOr5HxgdIaJOWesbBB2vba6ZHZlWYgzk8Xx1x/RXP14/wDUtWlu4V81W67laAQ9NepvssZgxUYG4duAeeAAefLnPHpjor3OzR0ue0odbqevK9mRldpPq3e2B5egn5QT9Vb/AJCalODwHhmhGNRpaijjejB2s31t2MjKxIB/8HIzvQEREBERAREQEREBERAREQEREBERAREQEREBBiDAREQEREBERATP9XrFst1Ow5DalnLYIDrsRUYZ7VwOR7D2iWnjWowq6dWKm5XLuCQU06Y6xge5vOVR3jdnulH4grWXJ1A2X2MtVSrgLs/qowxjao5+oBiO+B9+A6NdRq3psawJjUWEIxQll6gDmOf9duXrnePBNF1w0+dRvNRt/wDntwFDBfHtyf8AAzm8GqXS8Tvrd92ym8F9u3cWGkbsGcds69jOMalFZma9lVCCCaihrQepSwV89wYy1MZc925NM4h+/wCjOl8dR+8W/fPnZ0f0isqs14Z2KoDqLcswUsQOfgpPsnto1u2rN3OxX6lwiklrAcAhRk4Iw2O4GebWOXsru2Mq0NXtLqVy1loVzg/mqO3+8ZOFJu1YzEo/ozpfG/39v3yo7dupdMkhG1SKWOW2JqAqgnv5Ac5dNBxMMmbgyksWXCOQam85DkDt2soPrBlJ1VNjvq7qWIFT6p3wuXNJ1J3MN3YV5NzHYD3yKow1tV8X2tPRXWK+o1KbuZSliMHzrUBV2z2E7Woz9Y8Zapn/AAXzQq04Dg9dSWY+dcAdys3eHBZSfXntAl50epW6pLVztsRWUHkQCM4PrlWz7xEQEREBERAREQEREBERAREQEREBERASZEQEGTIMBETzW6+hCVe6pGGMq1iKR7CYHpiePyppvSKPe1/fHlTTekUe9r++MSnD2zz6m9KkL2sqovaWOBzOAPrPZjvzOdruNquE0xrvtbmcOOqqrH0rHYZ2juA7ST4AkVzi/F7DZp2d6SimwqK1sxXcVARi7cjyLgchgkeqMIebjnEa9RY7Wh02l1oWxLKWSlO10ZgDuc5JIPJVUHHOdnohwV0CazUMWuesipGUKaqmOQT4uRtzyGMkeOa67V2vSjuj7tRUTvdSuFcMxYk9mA2fHs75oPlTTekUe9T75PDKcK5oz/xvU/qrf4NHLNMz6W6yv5xeyiu5X1CYbalwVfm9eWUZwTyx9s5VTJZpnZU01VqvtV7KkUMvI524ODzI7/uRPXBV8auqjV+s4ao2iPzkXZGwDcUxz68AqHz+iSvsE+2s0wtqepsgWKykjGQCMZHrmM7H/tNF7lf9uOrf+00PuV/25b92zDQ6TG7bFXAAHIAYA8BKx0X567W9436of8y0pHErKa+rVKqW3IWd0pR/O5YAGeXeZZug2vrDb7DXQDp2XaStagizuBPLOM49cpnM4dEfGqooi5PaekPlxzgvzS5FLs2itLipPorXZzbqnOcsuM7fUrZzjJ7fRnjNSg0litJKtp7GSxaQXJDUq5G0gNzXBxhwo+jPR0ov01+itQWUWEGt9m+tiVSxWYAZ5nAYD65Wl1qIrkujVlSHTIZHQ8ipXvz2ScShpUiU/hXGNUunpU9Rc61V7q3Nld7EKMoWOVZ+7PIZnf0/GNLYquLq1yOaO6pYhBwVZScggggjxEjCHRiePyppvSKPe1/fHlTTekUe9r++MSnD2QZ8qbkddyOrjsyjBhn6xPqYQREQEmREBERAmJEQJiRECYkRAmJEQJkGIMBMd6WD/iOr/WD+BZsRmO9LPyjq/wBYP4Fm/wAfylpb7uPiSBETtbLA+qXS6WpEAL2olrd4LsoOT/dUHAHec+JM5Gq1z2hQ5AA7lGAT4mecsTjJJwABk5wB2D6pExt2ojrPdWKcdZ7kjEmJssREQEREBERAjE+lNhR1dcblORkAz8RE9e46p40+V8xQo+mMklvqPdPpx0JYlepTBZyUc97lQNrn+9jKn9ETjSdxxjJwMkDJxzxnl7B9gmOjEVRVCnDicw/OIxJibLtJ+Tb8Tu/an/l1y4GU/wCTb8Tu/am/l1y4Tz7nnLnq8pTEiJmqmJEQJiRECYkSYEREQEREBERAREQBmO9LPyjq/wBYP4FmwzHuln5R1f6wfwLOj4/lLS33ciIidjYyO/s78duJ2uknAxoXqQWG02IWyUCbRnAH0jnvnEbsP1GXD5SQet023keoOD/9plcrmmYx7/kpjirinOM7qa9ir2nH+ch7CDtVSx7fAfbPhUQp88EN+c3MH2z0k5yAeePsmFF2q5TM5xO0d4/t6VyxbsVRGJq9z2/D5i4ggOu3PZzBl54R0Np1NC3Lqyxcc9iDard6nJzkeyUJwVZC5388Dlgg+MvXyecT2XvpWPm3jengLVHMe1R/+BK0V3JiqJmcxP33wx/ULVNFNFdvHWOuO35c/gvR+vU6vUaY3OBRnawqILhW2knJ83u5Htz6p9NN0f0ttlwTiFa01YBexQrluecBmAK8vpd/+MsvSlqtDTqbaRt1OvYKTnmAFwzKO7kSf0mE5nyblWfUKa0LKEdbCoNi5yCu7w5A4+uacdU0zVl53FOMuZwboqdW1xr1NXVVWFA6qXdwOxtuRtU9xz3GcPiFApvup3buqtavONu7axGcd3ZNF6NflPi36VX/AFT38J1deqOu070IEp1NlbKACtoZjlmGO0kEn641qqZ69Y6HHMSyMmMzS+HaCrTcOstotFTuGY6wVfOGVN+B5o5kADHq5mea/XaK/W6C2hVusssaux2osVHTH0huABZT2HngE+qX185xCeP0z3cPGTNV47x7T6K9OtpZmek7bKwhcKG+hhiMDv7fZMu1Fgd3cKEDu7hF+igLEhR6hnHsl7dya+uMLU1Z+nziImizSfk2/E7v2pv5dcuEp/ybfid37U38uuXCefc85c9XlJERM1SIiAiIgIiICTIiBMSIgTIiICIiAMx3pZ+UdX+sH8CzYjMd6WflDV/rB/As6Pj+UtLfdyIiJ2Nj6+fq8Z0uM8Zt1rI9y1q1YKr1auuVJzg5YzmxIxGcmEMoIwRkeufh6VJzzB8QcGfSJWq3TV3jLWi/ctzmiZh8koUHJyxHYWOcT00XNW6WIdrIysp8GU5E+cRRbpojERgu3a7s5rnLo8b4zdrbFsu2jYmxVQEKozknBJ5n/QT78D6Q3aJXWpKW3sGLOGLchgDcCOXby9Z8Zx4k8FOOHHRjiMYdz+lOrW+y9DXW1uzrFSsbXCAhc7sn+seeZ+9V0q1LpYiLRR1xJuehCjuxGCSxJ7fHt9c4ESNOnZHDDtcG6TanRoaq9j1ZJVLVYhSe3aQQefhPo/SvVNqE1LipmrVlrrKHq0DY3Ec87jgc8zgxGnTnODhh2uN9JLtaipbXSoVtysiNvzjGMljgfcJxYiWppimMQmIiOxERJS0r5NvxO79pb+XXLeJUPk2/E7v2lv5dct88655y56vKSIiUVTEiICIiBMiIgIkyICJMiAiTECIkxAiZP0p4bqW1+pZNPe6M4KulTurDYvMEDBmsRiXt18E5WpqxLEvJWq9F1PuLfhjyVqvRdT7i34ZtsTbmZ2W1J2Yl5K1Xoup9xb8MeStV6LqfcW/DNtiOZnY1J2Yl5K1Xoup9xb8MeStV6LqfcW/DNtiOZnY1J2Yl5K1Xoup9xb8MeStV6LqfcW/DNtiOZnY1PTEvJWq9F1PuLfhjyVqvRdT7i34ZtsRzM7Gp6Yl5K1Xoup9xb8MeStV6LqfcW/DNtiOZnY1PTEvJWq9F1PuLfhjyVqvRdT7i34ZtsRzM7Gp6Yl5K1Xoup9xb8MeStV6LqfcW/DNtiOZnY1PTEvJWq9F1PuLfhjyVqvRdT7i34ZtsRzM7GpOyqfJ/prKtJYLa3rZtQzBbFZGK7EGcHnjkfslqkxOeqrimZUmczkiTIkIIkxAiJMQIiTEBERAiTEQEREBERAREQEREBERAREQEREBERAiTEQEREBERASJMQEREBERAREQEREBIkxA//9k=',
    auth_token='4fe7da620427e2ad-e463e2a4e06c3b42-e38192c60138840e'
))


@app.route('/', methods=['GET'])
def HOME():
    # print("--------------------------------HOME--------------------------------")
    return "<html><h1>Viber bot that gives Chuck Norris joke as reply of each message.</h1></html>"


@app.route('/', methods=['POST'])
def incoming():
    # logger.debug("received request. post data: {0}".format(request.get_data()))
    # print("--------------------------------{}--------------------------------".format(request.get_data()))

    try:
        # print("--------------------------------INSIDE TRY--------------------------------")
        viber_request = viber.parse_request(request.get_data())

        if isinstance(viber_request, ViberMessageRequest):
            message = retrieve_chuck_joke()
            viber.send_messages(viber_request.sender.id, [
                TextMessage(text=message)
            ])
        elif isinstance(viber_request, ViberConversationStartedRequest) \
                or isinstance(viber_request, ViberSubscribedRequest) \
                or isinstance(viber_request, ViberUnsubscribedRequest):
            viber.send_messages(viber_request.sender.id, [
                TextMessage(None, None, viber_request.get_event_type())
            ])
        elif isinstance(viber_request, ViberFailedRequest):
            logger.warning("client failed receiving message. failure: {0}".format(viber_request))

        # elif isinstance(viber_request, EventType.WEBHOOK):
            # logger.debug("WEBHOOKEVENTS: {0}".format(request.get_data()))
            # print("--------------------------------WEBHOOKEVENTS--------------------------------")
    except Exception as e:
        return "--------------------------------ERRRRRRRRRRRRRRRRRRRR--------------------------------" + str(e)

    return Response(status=200)

def set_webhook(viber):
    # print("--------------------------------SET WEBHOOK--------------------------------")
    # I used heroku as it is easier and serves over https
    viber.set_webhook('https://viberbotfree.herokuapp.com/', [EventType.WEBHOOK, EventType.CONVERSATION_STARTED, EventType.DELIVERED, EventType.MESSAGE, EventType.SUBSCRIBED, EventType.UNSUBSCRIBED, EventType.FAILED, EventType.SEEN])

@app.route('/chuckjoke', methods=['GET'])
def retrieve_chuck_joke(url="https://chucknorrisfacts.net/random-fact.php"):
    user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
    headers = {'User-Agent': user_agent}
    joke_txt = ""

    try:
        req = urllib.request.Request(url, None, headers)
        response = urllib.request.urlopen(req)
        html_page = response.read()
        response.close()
        soup_page = BeautifulSoup(html_page, "html.parser")
        joke_p = soup_page.find_all('p')
        joke_txt = joke_p[0].get_text()
    except Exception as e:
        logger.debug('Error fetching data from ' + url, e)

    return joke_txt

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1>"

if __name__ == "__main__":
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(13, 1, set_webhook, (viber,))
    t = threading.Thread(target=scheduler.run)
    t.start()

    app.run(host='0.0.0.0', port=int(os.getenv("PORT", "8443")), debug=True)
