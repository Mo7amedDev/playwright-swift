from playwright.async_api import Locator 
from typing import Literal
from .myContext import AsyncPage
import random
import asyncio
from .utils.bz_curve import bezier_curve
class HumanBehavior:

    def __init__(self,page:AsyncPage):
        self.page = page
        self.isInitialized = False

    async def __initialize(self):
        if self.isInitialized: return
        self.isInitialized = True
        await self.page.evaluate('''() => {
                window.mouseX = 0;
                window.mouseY = 0;
                document.addEventListener('mousemove', (event) => {
                    window.mouseX = event.clientX;
                    window.mouseY = event.clientY;
                });
            }''') 
    async def moveTo(self,element:Locator,steps=30,duration=random.randint(20,60),method:Literal["linear_noise","bezier_curve"]="linear_noise"):
        await self.__initialize()
        bounding_box = await element.bounding_box()
        if bounding_box is None:
            raise Exception("Element is not visible")
        mouse = self.page.mouse
        position = await self.page.evaluate("()=>({x:window.mouseX, y:window.mouseY})")
        x0 = position["x"]
        y0 = position["y"]

        center_x = bounding_box["x"] + bounding_box["width"] / 2
        center_y = bounding_box["y"] + bounding_box["height"] / 2

        dx = random.uniform(-bounding_box['width'] * 0.2, bounding_box['width'] * 0.2)  # Up to 20% of width
        dy = random.uniform(-bounding_box['height'] * 0.2, bounding_box['height'] * 0.2)  # Up to 20% of height

        x1 = center_x + dx
        y1 = center_y + dy

        if method == "linear_noise":
            dx = (x1 - x0) 
            dy = (y1 - y0) 
            f = random.randint(5,10)
            for i in range(steps):
                t = i/steps 
                offset_x = random.uniform(-f,f)
                offset_y = random.uniform(-f,f)
                x = x0 + dx * t + offset_x
                y = y0 + dy * t + offset_y
                await  mouse.move(x,y)
                await asyncio.sleep(duration/1000)

            await mouse.move(x1,y1)
        else:
            dx,dy = abs(x1-x0),abs(y1-y0)
            randomness = min(max(dx,dy) * 0.2, 50)

            control_points = [
                (x0, y0),
                (x0 + random.uniform(-randomness, randomness), y0 + random.uniform(-randomness, randomness)),
                (x1 + random.uniform(-randomness, randomness), y1 + random.uniform(-randomness, randomness)),
                (x1, y1)
            ]

            for i in range(steps):
                t = i/steps
                x,y = bezier_curve(t,control_points)
                await mouse.move(x,y)
                await asyncio.sleep(duration/1000)
        
            await mouse.move(x1,y1)
        return x1,y1 

    async def click(self,element:Locator,durationMov=random.randint(20,60),method:Literal["linear_noise","bezier_curve"]="linear_noise"):
        x,y = await self.moveTo(element,method=method,duration=durationMov)
        await self.page.mouse.click(x,y)

    async def type(self,element:Locator,text:str,method:Literal['uniform_delay','random_delay']="uniform_delay",delay=random.randint(20,100)):
        if(method == 'random_delay'):
            for char in text:
                await element.press(char)
                await asyncio.sleep(random.randint(10,delay)/1000)
        else:
            await element.press_sequentially(text, delay = delay)



 