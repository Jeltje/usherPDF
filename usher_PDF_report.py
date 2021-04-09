#!/usr/bin/env python
# coding: utf-8

#from fpdf import FPDF, HTMLMixin
from datetime import date
import collections
from myPDF import PDF

class SampleInfo:
    '''Mutations and closest strain info per sample'''
    def __init__(self, inline):
        '''Info extracted from a single line in usher_samples_hgwdev_angie_1a1b7_a247a0.tsv'''
        fields = inline.strip().split('\t')
        self.name = fields[0]
        self.neighbor = fields[15]
        self.hasIssue = 'None'
        self.muts = fields[2]
        if self.muts != '':
            self.splitMuts()
        else:
            self.spikeMuts = []
    def splitMuts(self):
        '''Extract the mutations per spike protein (S:)'''
        spikeMuts = set()
        byORF = self.muts.split(',')
        for combi in byORF:
            orf, mut = combi.split(':')
            if orf == 'S':
                spikeMuts.add(mut.lstrip('S:'))
        self.spikeMuts = list(spikeMuts)
    

class Vset:
    '''Holds and manipulates SampleInfo objects'''
    def __init__(self):
        self.entries = []
    def add(self, inline):
        v = SampleInfo(inline)
        self.entries.append(v)
    def variantTableIfHits(self, strains, strainIssue, printAll=False):
        '''Check if the sample neighbors match any of a list of variants
           and if so, add that info to the sample and create a table.
           Return positioning info for text'''
        sampleCount = len(self.entries)
        # first we must know if we have any hits at all
        matchingSampleCount = len([v for v in self.entries if v.neighbor in strains.keys()])
        if matchingSampleCount == 0:
            return(pdf.get_x(), 0)
        # strains is a dict with variant as key, location of origin as value
        header = ["Variant", "First detected      ", "Samples", "Frequency"]
        colWidths = pdf.buildTable(header, isHead=True)
        for variant, location  in strains.items():
            matchingSamples = [v for v in self.entries if v.neighbor == variant]
            # add issue to the sample object
            for v in matchingSamples:
                v.hasIssue = strainIssue
            hitCount = len(matchingSamples)
            # print only variants that have sample hits...
            if(hitCount > 0):
                fract = round((float(hitCount)/sampleCount), 2)
                pdf.buildTable([variant, location, str(hitCount), str(fract)], colWidths)
            # ... unless otherwise instructed
            elif(printAll == True):
                pdf.buildTable([variant, location, '0', '0'], colWidths)
        return(sum(colWidths) + 15, matchingSampleCount)
    def mutationTable(self, mutations, printAll=False):
        '''Match mutations of concern to samples that are not already classified; output table'''
        remainingSamples = [v for v in self.entries if v.hasIssue == 'None']
        if len(remainingSamples) == 0:
            return(pdf.get_x(), 0)
        # if none of the remaining samples has any matching mutations, don't print table
        for mutation, variant in mutations.items():
            matchingSamples = [v for v in remainingSamples if mutation in v.spikeMuts]
            for v in matchingSamples:
                v.hasIssue = 'Mutation of Concern'
        matchingUniqSampleCount = len([v for v in self.entries if v.hasIssue == 'Mutation of Concern'])
        if matchingUniqSampleCount == 0:
            return(pdf.get_x(), 0)
        # we have at least some, so print a table
        header = ["Mutation", "Found in                         ", "Samples"]
        colWidths = pdf.buildTable(header, isHead=True)
        for mutation, variant in mutations.items():
            matchingSamples = len([v for v in remainingSamples if mutation in v.spikeMuts])
            if (matchingSamples > 0) or printAll == True:
                pdf.buildTable([mutation, variant, str(matchingSamples)], colWidths)
        return(sum(colWidths) + 15, matchingUniqSampleCount)
    def perSampleTable(self):
        '''On a new page(?), put all the samples, nearest neihbor, and their issue (if any)'''
        # need to know the longest names to size the header
        header = ["Sample name", "Closest known variant", "Class"]
        pdf.set_font('Times', '', 10)
        sSize = 5 + pdf.get_string_width(max([v.name for v in self.entries], key = len))
        nSize = 5 + pdf.get_string_width(max([v.neighbor for v in self.entries]+header, key = len))
        cSize = 5 + pdf.get_string_width(max([v.hasIssue for v in self.entries], key = len))
        colWidths = [sSize, nSize, cSize]
        pdf.buildTable(header, colWidths=colWidths, isHead=True)
        for v in self.entries:
            pdf.buildTable([v.name, v.neighbor, v.hasIssue], colWidths)


####################################
### Main                         ###
####################################

ushStrain = 'usher_samples_hgwdev_angie_1a1b7_a247a0.tsv'
outf='/mnt/c/Users/yinna/Downloads/play/my.pdf'

vList = Vset()
with open(ushStrain, 'r') as f:
    head = f.readline()
    for line in  f:
        vList.add(line)

# start printing the PDF
pdf = PDF()
# total number of pages, put in {nb}
pdf.alias_nb_pages()
# auto adds as many pages as needed
pdf.add_page()
pdf.set_font('Times', '', 12)

####################################
### General info section         ###
####################################

pdf.chapter("Introduction")
intro = ['This is a summary of the UShER analysis of', str(len(vList.entries)), 'samples analyzed on', str(date.today()), 
     '. The full analysis can be found']
pdf.txtWithUrl('This is a summary of the', 'UShER', 'https://genome.ucsc.edu/cgi-bin/hgPhyloPlace', 'analysis of', newline=False)
beforeTxt = " {} samples analyzed on {}. The full analysis can be found".format(len(vList.entries), date.today())
pdf.txtWithUrl(beforeTxt, "at UCSC", "https://genome.ucsc.edu/cgi-bin/hgPhyloPlace", "(this is a placeholder link)")

####################################
### Variants of Concern section  ###
####################################

# We want the number of samples in the title so create a placeholder for now
xloc, yloc = pdf.chapterSpace()

# Variants of concern and their locations of origin
vocs = {'B.1.1.7': 'United Kingdom', 
	'P1': 'Japan/Brazil', 
	'B.1.351': 'South Africa', 
	'B.1.427': 'California', 
	'B.1.429': 'California'}

# if any variant is in our set, print table and keep track of where it ends...
y_offset = pdf.get_y()
x_offset, hitCount = vList.variantTableIfHits(vocs, 'Variant of Concern', printAll=True)
endOfTable = pdf.get_y()

intro = 'These variants have changes in the spike protein for which there is evidence of one or more of the following: '
bullet_text = ['an increase in transmissibility',
            'more severe disease (increased hospitalizations or deaths)', 
            'significant reduction in neutralization by antibodies generated during previous infection or vaccination',
            'reduced effectiveness of treatments or vaccines', 
            'diagnostic detection failures']

# ... so we can print the text next to it
pdf.printPar(intro, bullet_text, x_offset, y_offset)
endOfText = pdf.get_y()
# make sure we start below the table OR the text, whichever is lower on the page
# TODO: check what happens on a page break
pdf.set_y(max(endOfTable, endOfText))

# fill the chapter space we created earlier
title = 'Variants of Concern: None found'
if hitCount > 0:
    title = 'Variants of Concern: {} samples'.format(hitCount)
pdf.chapterFill(title, xloc, yloc)

# add a URL for more information
pdf.cdc_link('Concern')

####################################
### Variants of Interest section ###
####################################

xloc, yloc = pdf.chapterSpace()

# variants of interest
vocs = {'B.1.526': 'New York', 
	'B.1.525': 'New York', 
	'P.2': 'Brazil'}

y_offset = pdf.get_y()
x_offset, hitCount = vList.variantTableIfHits(vocs, 'Variant of Interest', printAll=True)
endOfTable = pdf.get_y()

intro = 'These variants have specific genetic markers that have been associated with one or more of the following:'
bullet_text = ['changes to receptor binding',
               'reduced neutralization by antibodies generated against previous infection or vaccination',
               'reduced efficacy of treatments', 
               'potential diagnostic impact',
               'predicted increase in transmissibility or disease severity' ]
pdf.printPar(intro, bullet_text, x_offset, y_offset)
endOfText = pdf.get_y()
pdf.set_y(max(endOfTable, endOfText))

# fill the chapter space we created earlier
title = 'Variants of Interest: None found'
if hitCount > 0:
    title = 'Variants of Interest: {} samples'.format(hitCount)
pdf.chapterFill(title, xloc, yloc)

# add a URL for more information
pdf.cdc_link('Interest')


####################################
### Mutations of Concern section ###
####################################
# If samples are not in either group they may still have 'mutations of concern', namely the individual
# mutations listed in the Variants of Concern table (so only spike proteins for now)

xloc, yloc = pdf.chapterSpace()

# Mutations of interest and the variants they occur in
mocs = collections.OrderedDict([
        ('D614G', 'all Variants of Concern'),
        ('N501Y', 'B.1.1.7; P1; B.1.351'),
        ('A570D', 'B.1.1.7'),
        ('P681H', 'B.1.1.7'),
        ('K417N', 'B.1.351'), 
        ('E484K', 'B.1.351'), 
        ('S13I',  'B.1.429'),
        ('W152C', 'B.1.429'),
        ('L452R', 'B.1.427; B.1.429')
       ])
y_offset = pdf.get_y()
x_offset, hitCount = vList.mutationTable(mocs)
endOfTable = pdf.get_y()

intro = 'If samples are not in either group they may still have mutations of concern: the individual spike protein mutations listed in the Variants of Concern table at CDC. Samples may have more than one such mutation; the total number of samples with any mutation is {}.'.format(hitCount)

pdf.printPar(intro, [], x_offset, y_offset)
endOfText = pdf.get_y()
pdf.set_y(max(endOfTable, endOfText))

# fill the chapter space we created earlier
title = 'Mutations of Concern: None found'
if hitCount > 0:
    title = 'Mutations of Concern: {} unique samples'.format(hitCount)
pdf.chapterFill(title, xloc, yloc)

####################################
### Per sample info              ###
####################################

# Sample	Neighbor	Info
pdf.add_page()
vList.perSampleTable()

# and finally, print to file
pdf.output(outf, 'F')





