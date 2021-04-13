#!/usr/bin/env python2.7
# coding: utf-8

# must use 2.7 because pyfpdf is old

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def piePlot(labels, counts, total, outpng):
    '''Make a pie plot with samples divided into their Variants. Calculate the number of unassigned.'''
    # fractions
    counts.append(total - sum(counts))
    sizes = []
    # remove any groups that have 0 counts
    keeplabels = []
    keepcounts = []
    for c, l in map(None, counts, labels):
        if c > 0:
            keepcounts.append(c)
            keeplabels.append(l)

    #This rather idiotic function calculates the raw counts from the percentage
    #    which appears to be the only way to get them labeled in the wedges
    def func(pct, allvals):
        absolute = int(round(pct/100.*np.sum(allvals)))
        return "{:d}".format(absolute)

    plt.rc('axes', titlesize=15)
    fig1, ax1 = plt.subplots()
#   GI logo base color, lightening in steps
#   colors = [(40,72,124),(80,112,164),(120,142,204),(160, 192, 244)]
#   converted to hex (using Google's color picker)
    colors = ['#a0c0f4', '#5070a4', '#788ecc', '#28487c']
    ax1.pie(keepcounts, labels=keeplabels, autopct=lambda pct: func(pct, keepcounts),
        shadow=False, colors=colors, counterclock=True, 
        wedgeprops = {"edgecolor" : '#002054', # almost black but still in GI color family
                      'linewidth': 0.5,
                      'antialiased': True})
    ax1.axis('equal')
    ax1.set_title("Sample types")
    plt.savefig(outpng, transparent=True)


