#command to run server on network: flask run --host=0.0.0.0
#i over-document my code because i'm a beginner and i want to make sure i understand whats going on, also at times id be lost without the documentation
#shoutout to github copilot




#IMPORTS
import time

#general flask imports
from flask import Flask, render_template, Response, request

app = Flask(__name__) #creates flask app instance

#import threading to loop the data read function that will also write to the file
import threading

#ofc manage serial connections
import serial



try:
    mBot = serial.Serial("COM3",115200,timeout=None) #port will always be com3, always using that baudrate for whatever reason lol and then timeout NONE because it just waits for the next byte to be read no matter what
except:
    raise Exception("Robot serial port not connected.") #ensures the bot is connected at server startup



#log server startup
with open("logFile.txt",'wt') as logFile:
    logFile.write("Program Run | " + time.strftime("%H:%M:%S", time.localtime()) + "\n")

def readLoop(): #this function will run in the bg forever
    line = ""
    while True:
        if mBot.isOpen() == False:
            raise Exception("Bot disconnected")
        curByte = str(mBot.read())[2:-1] #reads current byte (since timeout is none, this will always just wait until a byte is passed and then read it) (also a byte is always passed as "b'<char>'" and ofc the b' and ' are useless so thats why it's [2:-1])
        if curByte == "\\r": #/r signals the end of a line
            mBot.read() #/n appears after every /r so read it to just get it out of the way since its useless
            if line.rfind("\\x") == -1:
                logToFile(line + "\n") #writes the newly read line of text to the file, allowing the user to view it on the webpage once it updates (also gets rid of the junk that gets sent at the start using the .find)
            else:
                logToFile(line[line.rfind("\\x") + 4:] + "\n") #does the same as the line above but gets rid of the junk that gets sent at the start using the .find if the junk is found
            line = "" #reset line back to nothing
        else:
            line += curByte #also keep in mind that this will not allow the message to show to the user until the full message is passed. this is necessary since the log file reader only updates the newest line when a new line is added (probably could work around for more read time updating but who cares)

# readloop will stop everything since most of its time will be spent waiting for bytes to read, so do it in a seperate thread. also its literally a while true loop lol
background_thread = threading.Thread(target=readLoop)
background_thread.start()



#below is the file writing/logging function (just for abstraction)
def logToFile(logItem):
    with open("logFile.txt", "at") as logFile: #'at' stands for "append text file"
        logFile.write(str(logItem))



#exact same as project6pwp since it doesnt need to be different
@app.route('/log') #endpoint for the stream of log data
def log():
    def generate(): #generator function
        with open('logFile.txt', 'r') as logFile: #open the log file
            last_pos = logFile.tell() #get the last position of the file (where the last line was)
            while True:
                line = logFile.readline() #read the last line
                if not line: #if there is no new line, wait .1 seconds and try again
                    time.sleep(.1)
                    logFile.seek(last_pos) #go back to the last position
                else:
                    last_pos = logFile.tell() #get the new position
                    yield 'data: {}\n\n'.format(line.strip()) #return the new line
    return Response(generate(), mimetype='text/event-stream') #text/event-stream is a media type that allows a server to send events to the client (sse, server sent events)



#main page
@app.route('/', methods=['GET', 'POST']) 
def dashboard(): 
    return render_template('dashboard.html') #passes the html page



#this is the only endpoint that will allow the user to interact directly with the robot, think of it as basically the serial monitor lol
@app.route("/write", methods = ['GET','POST'])
def write():
    writeContents = request.args.get('content', default = "q") #gets the query passed by the user for what they wanna write through serial
    mBot.write(bytearray(writeContents, "ascii")) #actually writes the bytes of the passed string to serial
    #add something that will prevent writes including back slashes since that would probably interfere with the arduino side program
    return "<p>write</p>"





if __name__ == '__main__': #some sort of thing that makes it so it always runs threaded and on the network but i dont think it works whatever i still run flask run --host=0.0.0.0
    app.run(host='0.0.0.0', threaded=True)
