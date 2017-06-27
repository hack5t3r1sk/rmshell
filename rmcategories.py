#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
from rmhelpers import *
from rmcategory import RMCategory

class RMCategories:
    def __init__(self, browser, categoriesURL):
        self.browser = browser
        self.BS = None
        self.categories = []
        self.list = []
        self.href = categoriesURL
        breaker = 0
        
        # Get the HTML
        rmlog(u'RMCategories::init()', u'getting categories.', 'debug3')

        self.BS = self.browser.getBeautifulSoup(self.browser.getURL(self.href, clean=False))
        
        if self.BS and len(self.BS) >0:
            # Parse the soup for DIVs with class="tile"
            for catdiv in self.BS('div', {'class': "tile"}):
                # DEBUG
                # Uncomment to limit the number of categories
                #breaker += 1
                if breaker >2:
                    break
                else:
                    #print catdiv
                    #print dir(catdiv)
                    # Get the category object from the sub-soup
                    tmpCat = RMCategory(catdiv, self.BS, self.browser)
                    if tmpCat.title:
                        self.categories.append(tmpCat)

        # Update our categories list
        self.list = [cat.title for cat in self.categories]
        # unset browser for serializing, it is a thread
        self.browser = None
        rmlog(u'RMCategories::init()', u'end of getCategories().', 'debug3')
        
    def __len__(self):
        return len(self.categories)
        
    def __getitem__(self, index):
        return self.categories[index]

    def get(self):
        return self.categories
