import asyncio
import websockets
import json
import time
import base64
from PIL import Image
import io
from typing import Literal, Coroutine

class HumanCaptchaSolver:
    """Class to solve captchas using WebSockets with human assistance."""
    
    # Constants
    CANVAS_WIDTH, CANVAS_HEIGHT = 0, 0
    SOLVED, FAILED, TIMEOUT = 1, 2, 0
    
    
    @staticmethod
    def _resize_image(image_bytes):
        """Resizes the image while maintaining aspect ratio."""
        image = Image.open(io.BytesIO(image_bytes))
        original_width, original_height = image.size
        
        max_width = min(original_width - 30, HumanCaptchaSolver.CANVAS_WIDTH - 30)
        max_height = min(original_height - 50, HumanCaptchaSolver.CANVAS_HEIGHT)

        image.thumbnail((max_width, max_height))
        resized_width, resized_height = image.size

        # Convert resized image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=70)
        
        scale_x = original_width / resized_width
        scale_y = original_height / resized_height

        return buffer.getvalue(), scale_x, scale_y
    
    @staticmethod
    async def _get_clip_region(element, is_capturing_page: bool):
        """Returns the clip region for capturing the screenshot."""
        if is_capturing_page:
            size = element.viewport_size
            return {'x': 0, 'y': 0, 'width': size['width'], 'height': size['height']}
        
        bounding_box = await element.bounding_box()
        return {
            'x': bounding_box["x"],
            'y': bounding_box["y"],
            'width': bounding_box["width"],
            'height': bounding_box["height"]
        }

    @staticmethod
    async def solve(page, captcha_element, on_click: Coroutine = None,URI = 'ws://localhost:3001'):
        """Solves the captcha by communicating over WebSockets."""
        
        is_sending_image = False
        is_capturing_page = False
        solve_state = HumanCaptchaSolver.TIMEOUT
        scale_x = scale_y = 1
        x_offset = y_offset = 0

        async def send_image(ws):
            """Captures and sends captcha image to the WebSocket server."""
            nonlocal is_sending_image, is_capturing_page, solve_state, scale_x, scale_y, x_offset, y_offset
            
            start_time = time.time()

            while True:
                if not is_sending_image:
                    await asyncio.sleep(1)
                    if time.time() - start_time > 50:
                        await ws.close()
                        return HumanCaptchaSolver.TIMEOUT
                    continue
                
                if solve_state != HumanCaptchaSolver.TIMEOUT:
                    break

                await page.bring_to_front()
                
                if solve_state in [HumanCaptchaSolver.FAILED, HumanCaptchaSolver.SOLVED]:
                    return solve_state

                clip_region = await HumanCaptchaSolver._get_clip_region(
                    page if is_capturing_page else captcha_element,
                    is_capturing_page 
                )

                try:
                    screenshot_bytes = await page.screenshot(clip=clip_region, type='jpeg')
                except:
                    is_capturing_page = True
                    clip_region = await HumanCaptchaSolver._get_clip_region(page, 'page')

                x_offset, y_offset = clip_region['x'], clip_region['y']
                resized_bytes, scale_x, scale_y = HumanCaptchaSolver._resize_image(screenshot_bytes)

                # Encode image to Base64 and send over WebSocket
                message = json.dumps({'type': 'image', 'value': base64.b64encode(resized_bytes).decode("utf-8")})
                try:
                    await ws.send(message)
                except Exception as e:
                    print(f"Error sending image: {e}")

                await asyncio.sleep(1)

        async def receive_messages(ws):
            """Receives and processes messages from the WebSocket server."""
            nonlocal is_sending_image, is_capturing_page, solve_state, scale_x, scale_y, x_offset, y_offset
            
            async for message in ws:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    print("❌ Invalid JSON received!")
                    continue

                match data.get('type'):
                    case 'dimen':
                        HumanCaptchaSolver.CANVAS_WIDTH = data.get('width')
                        HumanCaptchaSolver.CANVAS_HEIGHT = data.get('height')
                    case 'sendImage':
                        is_sending_image = True
                        HumanCaptchaSolver.CANVAS_WIDTH = data.get('width')
                        HumanCaptchaSolver.CANVAS_HEIGHT = data.get('height')
                    case 'click':
                        x = data.get('x') * scale_x + x_offset
                        y = data.get('y') * scale_y + y_offset
                        await (on_click(x, y) if on_click else page.mouse.click(x, y))
                    case 'page':
                        is_capturing_page = True
                    case 'captcha':
                        is_capturing_page = False
                    case 'success':
                        solve_state = HumanCaptchaSolver.SOLVED
                        is_sending_image = True
                        print("🎉 Success! Closing WebSocket...")
                        await ws.close()
                        break
                    case "fail":
                        solve_state = HumanCaptchaSolver.FAILED
                        is_sending_image = True
                        print("❌ Failed! Closing WebSocket...")
                        await ws.close()
                        break
                    case 'wait':
                        is_sending_image = False

        async with websockets.connect(URI) as ws:
            await ws.send(json.dumps({'role': 'client'}))
            await asyncio.gather(receive_messages(ws), send_image(ws))

            return solve_state

# --- Main Execution ---
if __name__ == '__main__':

    async def on_click(x, y):
        """Simulated click function."""
        print(f"Clicking at: ({x}, {y})")

    async def main():
        result = await HumanCaptchaSolver.solve(None, None, on_click)
        
        if result == HumanCaptchaSolver.SOLVED:
            print("Captcha solved successfully!")
        else:
            print("Captcha failed or timed out.")

    asyncio.run(main())
