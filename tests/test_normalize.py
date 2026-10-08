"""Content normalization and hashing tests."""

import unittest

from radar.normalize import content_hash, normalize


class NormalizeTests(unittest.TestCase):
    def test_strips_html_and_keeps_text(self):
        html = "<p>Hello <b>world</b></p>"
        self.assertEqual(normalize(html), "Hello world")

    def test_removes_nav_header_footer_script(self):
        html = """
        <html><head><script>evil()</script><style>.x{}</style></head>
        <body><nav>Menu</nav><header>Site header</header>
        <article><p>Body text.</p></article>
        <footer>Site footer</footer></body></html>
        """
        text = normalize(html)
        self.assertIn("Body text.", text)
        for noise in ("evil()", "Menu", "Site header", "Site footer"):
            self.assertNotIn(noise, text)

    def test_collapses_whitespace_deterministically(self):
        messy = "Line   one\r\n\r\n\r\n\tLine   two  "
        clean = normalize(messy)
        self.assertEqual(clean, "Line one\nLine two")
        self.assertEqual(normalize(messy), clean)

    def test_plain_text_passes_through(self):
        self.assertEqual(normalize("plain abstract text"), "plain abstract text")

    def test_entities_unescaped(self):
        self.assertEqual(normalize("<p>Q&amp;A &lt;tag&gt;</p>"), "Q&A <tag>")

    def test_malformed_html_does_not_lose_all_content(self):
        text = normalize("<p>Broken <b>bold <i>item</p>")
        self.assertIn("Broken", text)
        self.assertIn("bold", text)


class ContentHashTests(unittest.TestCase):
    def test_hash_is_stable(self):
        self.assertEqual(content_hash("abc"), content_hash("abc"))

    def test_hash_differs_for_different_content(self):
        self.assertNotEqual(content_hash("abc"), content_hash("abd"))

    def test_identical_normalized_content_same_hash(self):
        a = normalize("<p>Same   content</p>")
        b = normalize("<p>Same content</p>")
        self.assertEqual(content_hash(a), content_hash(b))

    def test_hash_is_sha256_hex(self):
        h = content_hash("x")
        self.assertEqual(len(h), 64)
        int(h, 16)  # valid hex


if __name__ == "__main__":
    unittest.main()
