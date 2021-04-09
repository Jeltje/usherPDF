#!/usr/bin/env python
# coding: utf-8

from fpdf import FPDF, HTMLMixin

class PDF(FPDF, HTMLMixin):
    '''PDF formatting for UShER report'''
    def header(self):
        # Logo
        self.image('GI.png', x=0, y=5, w=66)
        # Line break
        self.ln(15)
    def buildTable(self, text, colWidths=False, isHead=False):
        '''Create one line in a table using two lists defining text and column width, 
           isHead makes bold and calculates colWidths, which are then returned'''
        self.set_font('Times','',10.0)
        # 40, 72, 124 is (almost) CGI logo color. 
        self.set_draw_color(40, 72, 124)  
        if isHead == True:
            # Add 120 to all GI color values to lighten it and use as background in table header
            self.set_fill_color(160, 192, 244)  
            self.set_font('Times','B',10.0)
            if colWidths == False:
                colWidths = [self.get_string_width(tx) + 2 for tx in text]
            #colWidths = []
            #for tx in text:
            #    colWidths.append(self.get_string_width(tx)+2)
        th = self.font_size
        for tx, cw in map(None, text, colWidths):
            self.cell(cw, 2 * th, tx, border=1, fill=True)
        self.set_font('Times','',10.0)
        self.ln(2 * th)
        # reset the background color
        self.set_fill_color(255, 255, 255)  # white
        if isHead == True:
            return colWidths
    def chapterSpace(self):
        '''Creates some spacing and returns placeholder coordinates 
        to fill in once we know the number of samples'''
        self.set_draw_color(40, 72, 124)  
	# create some distance
        self.ln(h = '10')
	# draw a line
        self.line(self.l_margin, self.y, self.w - self.r_margin, self.y)
        self.ln(h = '10')
        # Create title space but print no text. This creates spacing for later
        xloc = self.get_x()
        yloc = self.get_y()
        self.set_font('Arial', 'B', 15)
        self.cell(w=50, h=10, txt='', border=0, ln=1)
        return xloc, yloc
    def chapterFill(self, title, xloc, yloc):
        '''Fill the chapter space with text'''
        # where are we now
        xcur = self.get_x()
        ycur = self.get_y()
        # go to correct location
        self.set_xy(x=xloc, y=yloc)
        # print title
        self.set_text_color(40, 72, 124)
        #self.set_text_color(100, 132, 184)  
        self.set_font('Arial', 'B', 15)
        self.cell(w=150, h=10, txt=title, border=0, ln=1)
        self.set_text_color(0, 0, 0)
        # and go back to where we started
        self.set_xy(x=xcur, y=ycur)
    def chapter(self, title):
        #self.set_text_color(100, 132, 184)  
        self.set_text_color(40, 72, 124)
        self.set_font('Arial', 'B', 15)
        self.cell(w=150, h=10, txt=title, border=0, ln=1)
        self.set_text_color(0, 0, 0)
    def printPar(self, intro, bullet_text, xloc, yloc):
        '''Formats an introduction line and a list of bullet points at an offset'''
        self.set_text_color(0, 0, 0)
        self.set_font('Times', '', 10)
        self.set_xy(xloc, yloc)
        self.multi_cell(w=0, h=5, txt=intro, border=0, align='L')
        for bt in bullet_text:
            self.set_x(xloc)
            self.multi_cell(w=0, h=5, txt='- '+ bt, border=0, align='L')
    def txtWithUrl(self, txtBefore, urltxt, url, txtAfter, newline=True):
        '''Adds one line containing a URL'''
        self.set_font('Times', '', 10)
        self.write(5, txtBefore + ' ')
        # Then put a blue underlined link
        self.set_text_color(0, 0, 255)
        self.set_font('Times', 'U', 10)
        self.write(5, urltxt, url)
        self.set_text_color(0, 0, 0)
        self.set_font('Times', '', 10)
        self.write(5, ' ' + txtAfter)
        if newline == True:
            self.ln(h = '10')
    def cdc_link(self, section):
        '''Link to section (Interest or Concern) on the CDC website'''
        self.set_font('Times', '', 10)
        cdcLink = "https://www.cdc.gov/coronavirus/2019-ncov/cases-updates/variant-surveillance/variant-info.html#" + section
        self.write(5, 'Visit ')
        # Then put a blue underlined link
        self.set_text_color(0, 0, 255)
        self.set_font('Times', 'U', 10)
        self.write(5, 'the CDC website', cdcLink)
        self.set_text_color(0, 0, 0)
        self.set_font('Times', '', 10)
        self.write(5, ' for more information')
        self.ln(h = '10')
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number (1/total)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

