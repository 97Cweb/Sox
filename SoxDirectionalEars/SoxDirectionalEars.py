#From https://stackoverflow.com/questions/8662999/writing-software-to-tell-where-sound-comes-from-directional-listening
import wave
import struct
from numpy import array, concatenate, argmax
from numpy import abs as nabs
from scipy.signal import fftconvolve
from matplotlib.pyplot import plot, show
from math import log
from math import asin

from pydub import AudioSegment


class SoxDirectionalEars():
    def __init__(self):
        pass

    def crossco(self,wav):
        """Returns cross correlation function of the left and right audio. It
        uses a convolution of left with the right reversed which is the
        equivalent of a cross-correlation.
        """
        cor = nabs(fftconvolve(wav[0],wav[1][::-1]))
        return cor

    #https://stackoverflow.com/questions/29547218/remove-silence-at-the-beginning-and-at-the-end-of-wave-files-with-pydub


    def trackTD(self,fname, width, chunksize=5000):
        track = []
        #opens the wave file using pythons built-in wave library
        wav = wave.open(fname, 'r')
        #get the info from the file, this is kind of ugly and non-PEPish
        (nchannels, sampwidth, framerate, nframes, comptype, compname) = wav.getparams ()

        print(framerate)
        #only loop while you have enough whole chunks left in the wave
        while wav.tell() < int(nframes/nchannels)-chunksize:
            
            #read the audio frames as asequence of bytes
            frames = wav.readframes(int(chunksize)*nchannels)
    
            #construct a list out of that sequence
            out = struct.unpack_from("%dh" % (chunksize * nchannels), frames)
    
            # Convert 2 channels to numpy arrays
            if nchannels == 2:
                #the left channel is the 0th and even numbered elements
                left = array (list (out[0::2]))
                #the right is all the odd elements
                right = array (list  (out[1::2]))
            else:
                left = array (out)
                right = left
    
            #zero pad each channel with zeroes as long as the source
            left = concatenate((left,[0]*chunksize))
            right = concatenate((right,[0]*chunksize))
    
            chunk = (left, right)
    
            #if the volume is very low (800 or less), assume 0 degrees
            print(max(abs(left)))
            if max(abs(left)) < 2000 or max(abs(left)) > 30000:
                a = 0.0
            else:
                #otherwise computing how many frames delay there are in this chunk
                cor = -argmax(self.crossco(chunk)) + 2*chunksize
                #calculate the time
                t = cor/framerate
                
                #get the distance assuming v = 340m/s sina=(t*v)/width
                sina = t*340/width
                a = asin(sina) * 180/(3.14159)
    
    
    
            #add the last angle delay value to a list
            track.append(a)
        return track
    

if __name__ == '__main__':
    direction  = SoxDirectionalEars()
    print(direction.trackTD("left.wav", 0.055))
    
        
