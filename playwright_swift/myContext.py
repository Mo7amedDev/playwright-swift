from undetected_playwright.async_api import async_playwright,Page,BrowserContext
import inspect
import asyncio

def tab(func):
    func._is_tab_decorated = True
    return func
 
class AsyncPage(Page):
    def __init__(self, impl_obj,*args,**kwargs):
        super().__init__(impl_obj)
        self.previousPage = None
        self.indexSide = 0
    async def focusToNewPage(self,pageClass:'AsyncPage',*args,**kwargs):
        obj:AsyncPage = pageClass(self._impl_obj,*args,**kwargs)
        self.previousPage = obj
        self.indexSide = 1
        return obj 
    async def _focus(self):
        async def _focus1(page:AsyncPage,__fromSide=0):
            if page.indexSide == 0: return
            else: 
                await _focus1(page.previousPage,page.indexSide)
                if page.indexSide == 1: await page.go_back()
                else : await page.go_forward()
                page.previousPage.previousPage = page
                page.previousPage.indexSide = -page.indexSide
                
                if __fromSide == 0:
                    page.previousPage = None
                    page.indexSide = 0
        await _focus1(self)
    async def open(self):
        self.goto("")


class MyBrowserContext:
    def __init__(self,context:BrowserContext):
        self.context = context
        self.isStart = False
    async def new_page(self, page_class:AsyncPage,*args,**kwargs):
        """Create a new page in the persistent context."""
        if not self.isStart: playwright_page = self.context.pages[0]
        else:playwright_page = await self.context.new_page()
        self.isStart = True
        return page_class(playwright_page._impl_obj,*args,**kwargs)
    async def start(self):
        tab_methods = []
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if hasattr(method, "_is_tab_decorated"):  # Check for the custom attribute
                tab_methods.append(method)
        await asyncio.gather(*[method() for method in tab_methods])
 


 