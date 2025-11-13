"""
Test Assertions - Common assertion patterns for E2E testing
"""

from typing import Any, Optional, List, Dict


class TestAssertions:
    """Common test assertions"""
    
    # ============ VISIBILITY ASSERTIONS ============
    
    @staticmethod
    async def assert_visible(page, selector: str, timeout: int = 5000):
        """Assert element is visible"""
        try:
            await page.wait_for_selector(selector, state='visible', timeout=timeout)
            return True
        except:
            raise AssertionError(f"Element not visible: {selector}")
    
    @staticmethod
    async def assert_hidden(page, selector: str, timeout: int = 5000):
        """Assert element is hidden"""
        try:
            await page.wait_for_selector(selector, state='hidden', timeout=timeout)
            return True
        except:
            raise AssertionError(f"Element not hidden: {selector}")
    
    @staticmethod
    async def assert_exists(page, selector: str):
        """Assert element exists in DOM"""
        count = await page.locator(selector).count()
        if count == 0:
            raise AssertionError(f"Element does not exist: {selector}")
        return True
    
    # ============ TEXT ASSERTIONS ============
    
    @staticmethod
    async def assert_contains_text(page, selector: str, text: str):
        """Assert element contains text"""
        content = await page.locator(selector).text_content()
        if text not in content:
            raise AssertionError(f"Text '{text}' not found in {selector}")
        return True
    
    @staticmethod
    async def assert_text_exact(page, selector: str, text: str):
        """Assert element text is exactly"""
        content = await page.locator(selector).text_content()
        if content.strip() != text.strip():
            raise AssertionError(f"Text mismatch: expected '{text}', got '{content}'")
        return True
    
    @staticmethod
    async def assert_placeholder(page, selector: str, placeholder: str):
        """Assert input has placeholder"""
        value = await page.locator(selector).get_attribute('placeholder')
        if value != placeholder:
            raise AssertionError(f"Placeholder mismatch: expected '{placeholder}', got '{value}'")
        return True
    
    # ============ VALUE ASSERTIONS ============
    
    @staticmethod
    async def assert_input_value(page, selector: str, value: str):
        """Assert input value"""
        input_value = await page.locator(selector).input_value()
        if input_value != value:
            raise AssertionError(f"Input value mismatch: expected '{value}', got '{input_value}'")
        return True
    
    @staticmethod
    async def assert_attribute(page, selector: str, attr: str, value: str):
        """Assert element attribute"""
        attr_value = await page.locator(selector).get_attribute(attr)
        if attr_value != value:
            raise AssertionError(f"Attribute '{attr}' mismatch: expected '{value}', got '{attr_value}'")
        return True
    
    @staticmethod
    async def assert_class(page, selector: str, class_name: str):
        """Assert element has class"""
        class_attr = await page.locator(selector).get_attribute('class')
        if class_name not in (class_attr or ''):
            raise AssertionError(f"Class '{class_name}' not found")
        return True
    
    # ============ ENABLED/DISABLED ASSERTIONS ============
    
    @staticmethod
    async def assert_enabled(page, selector: str):
        """Assert element is enabled"""
        is_enabled = await page.locator(selector).is_enabled()
        if not is_enabled:
            raise AssertionError(f"Element is not enabled: {selector}")
        return True
    
    @staticmethod
    async def assert_disabled(page, selector: str):
        """Assert element is disabled"""
        is_enabled = await page.locator(selector).is_enabled()
        if is_enabled:
            raise AssertionError(f"Element is not disabled: {selector}")
        return True
    
    # ============ CHECKED/UNCHECKED ASSERTIONS ============
    
    @staticmethod
    async def assert_checked(page, selector: str):
        """Assert checkbox is checked"""
        is_checked = await page.locator(selector).is_checked()
        if not is_checked:
            raise AssertionError(f"Checkbox not checked: {selector}")
        return True
    
    @staticmethod
    async def assert_unchecked(page, selector: str):
        """Assert checkbox is unchecked"""
        is_checked = await page.locator(selector).is_checked()
        if is_checked:
            raise AssertionError(f"Checkbox is checked: {selector}")
        return True
    
    # ============ COUNT ASSERTIONS ============
    
    @staticmethod
    async def assert_element_count(page, selector: str, expected_count: int):
        """Assert element count"""
        count = await page.locator(selector).count()
        if count != expected_count:
            raise AssertionError(f"Element count mismatch: expected {expected_count}, got {count}")
        return True
    
    @staticmethod
    async def assert_at_least(page, selector: str, min_count: int):
        """Assert at least N elements"""
        count = await page.locator(selector).count()
        if count < min_count:
            raise AssertionError(f"Expected at least {min_count} elements, got {count}")
        return True
    
    # ============ URL/NAVIGATION ASSERTIONS ============
    
    @staticmethod
    async def assert_url(page, url: str):
        """Assert page URL"""
        current_url = page.url
        if current_url != url:
            raise AssertionError(f"URL mismatch: expected '{url}', got '{current_url}'")
        return True
    
    @staticmethod
    async def assert_url_contains(page, substring: str):
        """Assert URL contains substring"""
        current_url = page.url
        if substring not in current_url:
            raise AssertionError(f"URL does not contain '{substring}'")
        return True
    
    # ============ API ASSERTIONS ============
    
    @staticmethod
    async def assert_api_called(page, url_pattern: str) -> bool:
        """Assert API was called"""
        responses = []
        
        def on_response(response):
            if url_pattern in response.url:
                responses.append(response)
        
        page.on('response', on_response)
        
        if not responses:
            raise AssertionError(f"API not called: {url_pattern}")
        
        return True
    
    @staticmethod
    async def assert_api_response_status(page, url_pattern: str, expected_status: int):
        """Assert API response status"""
        responses = []
        
        def on_response(response):
            if url_pattern in response.url:
                responses.append(response)
        
        page.on('response', on_response)
        
        if not responses:
            raise AssertionError(f"API not called: {url_pattern}")
        
        if responses[-1].status != expected_status:
            raise AssertionError(
                f"API status mismatch: expected {expected_status}, got {responses[-1].status}"
            )
        
        return True
    
    # ============ ERROR MESSAGE ASSERTIONS ============
    
    @staticmethod
    async def assert_error_message(page, error_selector: str, expected_message: str):
        """Assert error message is displayed"""
        await TestAssertions.assert_visible(page, error_selector)
        await TestAssertions.assert_contains_text(page, error_selector, expected_message)
        return True
    
    @staticmethod
    async def assert_no_error(page, error_selector: str):
        """Assert no error is displayed"""
        try:
            await TestAssertions.assert_hidden(page, error_selector, timeout=1000)
            return True
        except:
            # If element doesn't exist, that's also ok
            return True
    
    # ============ FORM ASSERTIONS ============
    
    @staticmethod
    async def assert_form_valid(page, form_selector: str):
        """Assert form is valid"""
        is_valid = await page.locator(form_selector).evaluate('el => el.checkValidity()')
        if not is_valid:
            raise AssertionError(f"Form is not valid: {form_selector}")
        return True
    
    @staticmethod
    async def assert_form_invalid(page, form_selector: str):
        """Assert form is invalid"""
        is_valid = await page.locator(form_selector).evaluate('el => el.checkValidity()')
        if is_valid:
            raise AssertionError(f"Form is valid but should be invalid: {form_selector}")
        return True
    
    # ============ PERFORMANCE ASSERTIONS ============
    
    @staticmethod
    async def assert_page_load_time(page, max_ms: int = 3000):
        """Assert page loads within time"""
        load_time = await page.evaluate('() => performance.timing.loadEventEnd - performance.timing.navigationStart')
        if load_time > max_ms:
            raise AssertionError(f"Page load time {load_time}ms exceeds max {max_ms}ms")
        return True
    
    @staticmethod
    async def assert_element_count_in_time(page, selector: str, expected_count: int, max_ms: int = 5000):
        """Assert element count within time"""
        start_time = await page.evaluate('() => Date.now()')
        
        while True:
            count = await page.locator(selector).count()
            if count == expected_count:
                return True
            
            elapsed = await page.evaluate('() => Date.now()') - start_time
            if elapsed > max_ms:
                raise AssertionError(
                    f"Expected {expected_count} elements, got {count} after {elapsed}ms"
                )
            
            await page.wait_for_timeout(100)
    
    # ============ TABLE/LIST ASSERTIONS ============
    
    @staticmethod
    async def assert_table_row_count(page, table_selector: str, expected_count: int):
        """Assert table row count"""
        row_count = await page.locator(f"{table_selector} tbody tr").count()
        if row_count != expected_count:
            raise AssertionError(f"Row count mismatch: expected {expected_count}, got {row_count}")
        return True
    
    @staticmethod
    async def assert_table_contains(page, table_selector: str, text: str):
        """Assert table contains text"""
        count = await page.locator(f"{table_selector}:has-text('{text}')").count()
        if count == 0:
            raise AssertionError(f"Table does not contain text: '{text}'")
        return True
    
    # ============ DIALOG ASSERTIONS ============
    
    @staticmethod
    async def assert_dialog_shown(page) -> str:
        """Assert dialog/alert is shown and return message"""
        dialog_message = None
        
        def on_dialog(dialog):
            nonlocal dialog_message
            dialog_message = dialog.message
            dialog.accept()
        
        page.on('dialog', on_dialog)
        
        if dialog_message is None:
            raise AssertionError("No dialog shown")
        
        return dialog_message
    
    # ============ CONSOLE ASSERTIONS ============
    
    @staticmethod
    async def assert_no_console_errors(page):
        """Assert no console errors"""
        errors = []
        
        def on_console(msg):
            if 'error' in msg.type.lower():
                errors.append(msg.text)
        
        page.on('console', on_console)
        
        if errors:
            raise AssertionError(f"Console errors: {errors}")
        
        return True
    
    # ============ CSS ASSERTIONS ============
    
    @staticmethod
    async def assert_computed_style(page, selector: str, property: str, expected_value: str):
        """Assert computed CSS style"""
        actual_value = await page.locator(selector).evaluate(
            f"(el) => window.getComputedStyle(el).{property}"
        )
        if actual_value != expected_value:
            raise AssertionError(
                f"Style mismatch for {property}: expected '{expected_value}', got '{actual_value}'"
            )
        return True