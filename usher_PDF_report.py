#!/usr/bin/env python
# coding: utf-8

#from fpdf import FPDF, HTMLMixin
from datetime import date
import collections
from myPDF import PDF


class SampleInfo:
    '''Mutations and closest strain info per sample; assign Variants of Concern or Interest
       and Mutations of Concern'''
    def __init__(self, inline, voConcern, voInterest, mutConcern):
        '''Info extracted from a single line in usher_samples_hgwdev_angie_1a1b7_a247a0.tsv'''
        fields = inline.strip().split('\t')
        self.name = fields[0]
        self.neighbor = fields[15]
        self.hasIssue = 'None'
        if self.neighbor in voConcern:
            self.hasIssue = 'Variant of Concern'
            return
        if self.neighbor in voInterest:
            self.hasIssue = 'Variant of Interest'
            return
        self.muts = fields[2]
        if self.muts != '':
            self.spikeMuts = self.splitMuts(mutConcern)
            if len(self.spikeMuts) > 0:
                self.hasIssue = 'Mutation of Concern' 
        else:
            self.spikeMuts = []
    def splitMuts(self, mutConcern):
        '''Extract the mutations per spike protein (S:) and find any matches with the
           mutations Of Concern'''
        spikeMuts = set()
        byORF = self.muts.split(',')
        for combi in byORF:
            orf, mut = combi.split(':')
            if orf == 'S':
                spikeMuts.add(mut.lstrip('S:'))
        return [m for m in list(spikeMuts) if m in mutConcern]

class VariantInfo:
   '''Per variant info (such as B.1.1.1.7 or N501Y)'''
   def __init__(self, name, location, issue):
       self.name = name
       self.loc  = location
       self.samples = []
       self.issue = issue
   def addSamples(self, listOfNames):
       '''Samples that match this variant'''
       self.samples = listOfNames
   def printTableLine(self, colWidths, totalSampleCount, mutation=False):
       '''Output a table in pdf format'''
       if mutation == True:
           pdf.buildTable([self.name, self.loc, str(len(self.samples))], colWidths)
           return
       hitCount = len(self.samples)
       fract = 0
       if hitCount > 0:
           fract = round((float(hitCount)/totalSampleCount), 2)
       pdf.buildTable([self.name, self.loc, str(hitCount), str(fract)], colWidths)
       
class VariantSet:
    '''Match a dictionary of variants to samples'''
    def __init__(self, samples, variantDict, isMutation=False):
        '''Inputs are sample table and a variant dictionary with name as key and location of origin as value'''
        self.isMutation = isMutation
        # mutations of concern table
        if isMutation == True:
            matchedSamples = [s for s in samples if s.hasIssue == 'Mutation of Concern']
        # variant of Concern/Interest
        else:
            matchedSamples = [s for s in samples if s.neighbor in variantDict.keys()]
        self.varList = []
        self.sCount   = len(matchedSamples)
        if self.sCount == 0:
            return
        self.totalSamples = len(samples)
        # extract the type of issue from one of the samples (Variant of Concern etc)
        self.issue = matchedSamples[0].hasIssue
        # Create a variant object and add the matching samples
        for variant, location  in variantDict.items():
            v = VariantInfo(variant, location, self.issue)
            if isMutation == True:
                v.addSamples([m for m in matchedSamples if variant in m.spikeMuts])
            else:
                v.addSamples([m for m in matchedSamples if m.neighbor == variant])
            self.varList.append(v)
        
    def tableIfHits(self):
        '''Print a table to the pdf if we have any hits for this variant set (Concern or Interest)'''
        if self.sCount == 0:
            return(pdf.get_x())
        if self.isMutation == True:
            header = ["Mutation", "Found in                         ", "Samples"]
        else:
            header = ["Variant", "First detected      ", "Samples", "Frequency"]
        colWidths = pdf.buildTable(header, isHead=True)
        for v in self.varList:
            v.printTableLine(colWidths, self.totalSamples, self.isMutation)
        return(sum(colWidths) + 15)


class SampleSet:
    '''Holds and manipulates SampleInfo objects'''
    def __init__(self):
        self.entries = []
    def add(self, inline, vocs, vois, mocs):
        v = SampleInfo(inline, vocs, vois, mocs)
        self.entries.append(v)
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
outf='/mnt/c/Users/yinna/Downloads/play/my2.pdf'

# Variants of concern and their locations of origin
vocs = {'B.1.1.7': 'United Kingdom', 
	'P1': 'Japan/Brazil', 
	'B.1.351': 'South Africa', 
	'B.1.427': 'California', 
	'B.1.429': 'California'}
# variants of interest
vois = {'B.1.526': 'New York', 
	'B.1.525': 'New York', 
	'P.2': 'Brazil'}

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

vList = SampleSet()
# add variant info to samples
with open(ushStrain, 'r') as f:
    head = f.readline()
    for line in  f:
        vList.add(line, vocs, vois, mocs)
# add sample info to variants
varConcern  = VariantSet(vList.entries, vocs)
varInterest = VariantSet(vList.entries, vois)
varMutConcern = VariantSet(vList.entries, mocs, isMutation=True)


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

title = 'Variants of Concern: None found'
if varConcern.sCount > 0:
    title = 'Variants of Concern: {} samples'.format(varConcern.sCount)
pdf.chapter(title)

# if any variant is in our set, print table and keep track of where it ends...
y_offset = pdf.get_y()
x_offset = varConcern.tableIfHits()
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

# add a URL for more information
pdf.cdc_link('Concern')

####################################
### Variants of Interest section ###
####################################

title = 'Variants of Interest: None found'
if varInterest.sCount > 0:
    title = 'Variants of Interest: {} samples'.format(varInterest.sCount)
pdf.chapter(title)

# if any variant is in our set, print table and keep track of where it ends...
y_offset = pdf.get_y()
x_offset = varInterest.tableIfHits()
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

# add a URL for more information
pdf.cdc_link('Interest')


####################################
### Mutations of Concern section ###
####################################
# If samples are not in either group they may still have 'mutations of concern', namely the individual
# mutations listed in the Variants of Concern table (so only spike proteins for now)

title = 'Mutations of Concern: None found'
if varMutConcern.sCount > 0:
    title = 'Mutations of Concern: {} samples'.format(varMutConcern.sCount)
pdf.chapter(title)

# if any variant is in our set, print table and keep track of where it ends...
y_offset = pdf.get_y()
x_offset = varMutConcern.tableIfHits()
endOfTable = pdf.get_y()


intro = 'If samples are not in either group they may still have mutations of concern: the individual spike protein mutations listed in the Variants of Concern table at CDC. Samples may have more than one such mutation; the total number of samples with any mutation is {}.'.format(varMutConcern.sCount)

pdf.printPar(intro, [], x_offset, y_offset)
endOfText = pdf.get_y()
pdf.set_y(max(endOfTable, endOfText))


####################################
### Per sample info              ###
####################################

# Sample	Neighbor	Info
pdf.add_page()
vList.perSampleTable()

# and finally, print to file
pdf.output(outf, 'F')





