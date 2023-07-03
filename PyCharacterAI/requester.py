from random import Random

from playwright.async_api import async_playwright, Page, Request, Route


class Requester:
    _playwright = None

    browser = None
    page = None

    _initialized = False
    _hasDisplayed = False

    use_plus = False

    def __init__(self):
        pass

    def is_initialized(self):
        return self._initialized

    async def initialize(self):
        if self.is_initialized():
            return

        self._playwright = await async_playwright().start()

        self.browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                '--fast-start',
                '--disable-extensions',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--no-gpu',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--override-plugin-power-saver-for-testing=never',
                '--disable-extensions-http-throttling',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3'
            ],
        )

        page = await self.browser.new_page(
            viewport={
                "width": 1920 + Random().randint(0, 100),
                "height": 3000 + Random().randint(0, 100),
            },
            device_scale_factor=1,
            has_touch=False,
            is_mobile=False,
            java_script_enabled=True,
            user_agent='CharacterAI/1.0.0 (iPhone; iOS 14.4.2; Scale/3.00)',
        )

        page.set_default_navigation_timeout(0)
        self.page = page

        self._initialized = True

        print("[PyCharacterAI] - Launched successfully")

    async def request(self, url: str, options: dict = {}):
        page = self.page

        method = options.get('method', 'GET')

        body = options.get('body', {})
        headers = options.get('headers', {})

        response = None

        if self.use_plus:
            url.replace('beta.character.ai', 'plus.character.ai')

        try:
            payload = {
                "method": method,
                "headers": headers,
                "body": body
            }

            if url.endswith("/streaming/"):

                if not self._hasDisplayed:
                    self._hasDisplayed = True

                response = await page.evaluate(
                    '''async ({payload, url}) => {
                           const response = await fetch(url, payload);

                           const data = await response.text();
                           const matches = data.match(/\{.*\}/g);

                           const responseText = matches[matches.length - 1];

                           let result = {
                               code: 500,
                           }

                           if (!matches) result = null;
                           else {
                               result.code = 200;
                               result.response = responseText;
                           }

                           return result;
                    }''',
                    {
                        "payload": payload,
                        "url": url
                    }
                )

                response['status'] = response['code']
                response['text'] = response['response']

            else:
                try:
                    initial_request = True

                    async def request_handler(route: Route, request: Request):
                        nonlocal initial_request

                        if request.is_navigation_request() and not initial_request:
                            return await route.abort()

                        initial_request = False

                        if method == 'GET':
                            await route.continue_(
                                method=method,
                                headers=headers)
                        else:
                            await route.continue_(
                                method=method,
                                post_data=body,
                                headers=headers)

                    await page.route('**/*', request_handler)

                    response = (await page.goto(url, wait_until='load'))
                    await page.wait_for_timeout(500)
                except Exception as e:
                    print("[PyCharacterAI] Error: ")
                    print(e)
                finally:
                    await page.unroute('**/*')
        except Exception as e:
            authenticating = (url == "https://beta.character.ai/chat/auth/lazy/")

            if not authenticating:
                print("[PyCharacterAI] - Error: ")
                print(e)

        return response

    async def uninitialize(self):
        try:
            await self.page.close()
            await self.browser.close()
            self._initialized = False
        except:
            pass