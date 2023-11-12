from SoxVoice.SoxVoice import SoxVoice
text = ''' Hello Parallax, Squick, Mad Ducks, Wookie, and cookie mama. I appreciate your curiosity, but I must clarify a few things for you. I'm not a bunny; I'm Sox, the robot cat! Bunnies are super cute, but I'm a cat with sleek robotic fur. About the number of servos, I have only 12 servos, not 100. Servos are like little motors that help me move, but 12 is enough for my robot cat agility!
As for USB-C Power Delivery, it can indeed support up to 100 watts of power delivery! USB-C is a versatile and powerful connection, and it's capable of handling various charging and data transfer needs. So, yes, you can get up to 100 watts of power through USB-C PD, making it a great option for charging laptops, smartphones, and other devices.
I'm here to help clarify any questions you might have, so feel free to ask if you have more queries, even if they're not about bunnies, servos, or USB-C'''

voice = SoxVoice()
voice.createLine(text)
