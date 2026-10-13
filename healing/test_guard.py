from .guard import check, mask_locators


def diff(old, new):
    return f"--- a/tests/bot.spec.ts\n+++ b/tests/bot.spec.ts\n-{old}\n+{new}\n"


def test_accepts_selector_repair():
    ok, _, _ = check(diff(
        "  await page.getByRole('button', { name: 'Ask' }).click();",
        "  await page.getByTestId('ask-button').click();",
    ))
    assert ok


def test_accepts_locator_repair_inside_expect():
    ok, _, _ = check(diff(
        "  await expect(page.locator('#answer')).toContainText('MySQL');",
        "  await expect(page.getByTestId('answer')).toContainText('MySQL');",
    ))
    assert ok


def test_accepts_chained_fallback_locator():
    ok, _, _ = check(diff(
        "  await page.getByRole('textbox').fill(q);",
        "  await page.getByRole('textbox').or(page.getByPlaceholder('Ask about Ghost')).fill(q);",
    ))
    assert ok


def test_rejects_changed_expected_value():
    ok, reason, _ = check(diff(
        "  await expect(page.getByTestId('answer')).toContainText('MySQL');",
        "  await expect(page.getByTestId('answer')).toContainText('SQLite');",
    ))
    assert not ok and "outside a locator" in reason


def test_rejects_weakened_matcher():
    ok, _, _ = check(diff(
        "  await expect(page.getByTestId('answer')).toContainText('MySQL');",
        "  await expect(page.getByTestId('answer')).toBeVisible();",
    ))
    assert not ok


def test_rejects_deleted_assertion():
    d = "--- a/t.ts\n+++ b/t.ts\n-  await expect(page.getByTestId('answer')).toContainText('MySQL');\n"
    ok, reason, _ = check(d)
    assert not ok and "added or removed" in reason


def test_rejects_test_marked_fixme():
    ok, reason, _ = check(diff(
        "test('answers a database question', async ({ page }) => {",
        "test.fixme('answers a database question', async ({ page }) => {",
    ))
    assert not ok and "fixme" in reason


def test_rejects_change_outside_locators():
    ok, _, _ = check(diff(
        "  await page.getByTestId('ask-button').click();",
        "  await page.getByTestId('ask-button').click({ force: true });",
    ))
    assert not ok


def test_mask_handles_nested_parens_and_quotes():
    line = "await expect(page.getByRole('button', { name: 'Ask (beta)' }).first()).toBeVisible();"
    assert mask_locators(line) == "await expect(<LOCATOR>).toBeVisible();"
