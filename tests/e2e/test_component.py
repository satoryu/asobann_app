import pytest
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import Select

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from selenium.common.exceptions import NoSuchElementException

from .helper import compo_pos, Rect, GameHelper, TOP


C_A = 'PlayingCard S_A'
C_K = 'PlayingCard S_K'
C_Q = 'PlayingCard S_Q'

@pytest.mark.usefixtures("default_kits_and_components")

@pytest.mark.usefixtures("server")
class TestHandArea:
    def put_one_card_each_on_2_hand_areas(self, host, another):
        host.go(TOP)
        host.should_have_text("you are host")
        host.drag(host.component_by_name("usage"), 0, -200, 'lower right corner')
        host.menu.add_kit.execute()
        host.menu.add_kit_from_list("Playing Card")
        host.menu.add_kit_done()

        host.menu.add_my_hand_area.click()
        host.move_card_to_hand_area(host.component_by_name(C_A), 'host', (-100, 0))

        another.go(host.current_url)
        another.menu.join("Player 2")
        another.should_have_text("you are Player 2")

        another.menu.add_my_hand_area.click()
        another.move_card_to_hand_area(another.component_by_name(C_K), 'Player 2', (100, 0))

        host.double_click(host.component_by_name(C_A))
        another.double_click(another.component_by_name(C_K))

    def test_cards_in_hand_are_looks_facedown(self, browser: webdriver.Firefox, another_browser: webdriver.Firefox):
        host = GameHelper(browser)
        another = GameHelper(another_browser)
        self.put_one_card_each_on_2_hand_areas(host, another)

        # assert text
        assert '♠A' in host.component_by_name(C_A).face()
        assert '♠A' not in another.component_by_name(C_A).face()
        assert '♠K' not in host.component_by_name(C_K).face()
        assert '♠K' in another.component_by_name(C_K).face()

        # assert image
        assert 'card_up.png' in host.component_by_name(C_A).face()
        assert 'card_back.png' in another.component_by_name(C_A).face()
        assert 'card_back.png' in host.component_by_name(C_K).face()
        assert 'card_up.png' in another.component_by_name(C_K).face()

    def test_cannot_handle_cards_owned_by_someone_else(self, browser: webdriver.Firefox,
                                                       another_browser: webdriver.Firefox):
        host = GameHelper(browser)
        another = GameHelper(another_browser)
        self.put_one_card_each_on_2_hand_areas(host, another)

        # cannot move
        before = host.component_by_name(C_K).rect()
        host.drag(host.component_by_name(C_K), 20, 0)
        assert before == host.component_by_name(C_K).rect()

        before = another.component_by_name(C_A).rect()
        another.drag(another.component_by_name(C_A), 20, 0)
        assert before == another.component_by_name(C_A).rect()

        # cannot flip
        face = host.component_by_name(C_K).face()
        host.double_click(host.component_by_name(C_K))
        assert face == host.component_by_name(C_K).face()

        face = another.component_by_name(C_A).face()
        another.double_click(another.component_by_name(C_A))
        assert face == another.component_by_name(C_A).face()

    def test_up_card_in_my_hand_become_down_when_moved_to_others_hand(self, browser: webdriver.Firefox,
                                                                      another_browser: webdriver.Firefox):
        host = GameHelper(browser)
        another = GameHelper(another_browser)
        self.put_one_card_each_on_2_hand_areas(host, another)

        host.move_card_to_hand_area(host.component_by_name(C_A), 'Player 2')
        another.move_card_to_hand_area(another.component_by_name(C_K), 'host')

        # assert text
        assert '♠A' not in host.component_by_name(C_A).face()
        assert '♠A' in another.component_by_name(C_A).face()
        assert '♠K' in host.component_by_name(C_K).face()
        assert '♠K' not in another.component_by_name(C_K).face()

        # assert image
        assert 'card_back.png' in host.component_by_name(C_A).face()
        assert 'card_up.png' in another.component_by_name(C_A).face()
        assert 'card_up.png' in host.component_by_name(C_K).face()
        assert 'card_back.png' in another.component_by_name(C_K).face()

    def test_cards_on_hand_area_follows_when_hand_area_is_moved(self, browser: webdriver.Firefox,
                                                                another_browser: webdriver.Firefox):
        host = GameHelper(browser)
        another = GameHelper(another_browser)
        self.put_one_card_each_on_2_hand_areas(host, another)

        host_card = host.component_by_name(C_A)
        host_card_pos = host_card.pos()
        hand_area = host.hand_area(owner="host")
        host.drag(hand_area, -50, -100)
        time.sleep(0.1)  # moving with traylike is Level C user action, so it's safer to wait
        assert host_card_pos.left - 50 == host_card.pos().left
        assert host_card_pos.top - 100 == host_card.pos().top

        # host_card is still owned by host
        assert '♠A' in host.component_by_name(C_A).face()
        assert '♠A' not in another.component_by_name(C_A).face()

        host.double_click(host_card)
        assert '♠A' not in host.component_by_name(C_A).face()
        assert '♠A' not in another.component_by_name(C_A).face()

        host.double_click(host_card)
        assert '♠A' in host.component_by_name(C_A).face()
        assert '♠A' not in another.component_by_name(C_A).face()

    def test_many_cards_on_hand_area_move_with_the_area(self, browser: webdriver.Firefox,
                                                        another_browser: webdriver.Firefox):
        host = GameHelper(browser)
        another = GameHelper(another_browser)

        host.go(TOP)
        host.should_have_text("you are host")
        host.drag(host.component_by_name("usage"), 0, -200, 'lower right corner')
        host.menu.add_kit.execute()
        host.menu.add_kit_from_list("Playing Card")
        host.menu.add_kit_done()

        another.go(host.current_url)
        another.menu.join("Player 2")
        another.should_have_text("you are Player 2")

        host.menu.add_my_hand_area.click()
        c1, c2, c3 = "PlayingCard S_A", "PlayingCard S_K", "PlayingCard S_Q"
        host.move_card_to_hand_area(host.component_by_name(c1), 'host', (-100, 10))
        host.move_card_to_hand_area(host.component_by_name(c2), 'host', (0, 0))
        host.move_card_to_hand_area(host.component_by_name(c3), 'host', (75, -10))

        pos_before = [host.component_by_name(c).pos() for c in (c1, c2, c3)]
        host.drag(host.hand_area(owner="host"), 200, 300, grab_at=(-40, 0))
        pos_after = [host.component_by_name(c).pos() for c in (c1, c2, c3)]

        time.sleep(0.2)

        assert pos_before[0].left + 200 == pos_after[0].left and pos_before[0].top + 300 == pos_after[0].top
        assert pos_before[1].left + 200 == pos_after[1].left and pos_before[1].top + 300 == pos_after[1].top
        assert pos_before[2].left + 200 == pos_after[2].left and pos_before[2].top + 300 == pos_after[2].top

        pos_another = [another.component_by_name(c).pos() for c in (c1, c2, c3)]
        assert pos_after == pos_another

    def test_resizing_hand_area_updates_ownership(self, browser: webdriver.Firefox, another_browser: webdriver.Firefox):
        host = GameHelper(browser)
        another = GameHelper(another_browser)
        self.put_one_card_each_on_2_hand_areas(host, another)

        host.double_click(host.component_by_name(C_Q))
        time.sleep(0.1)  # prevent unintended double clicking
        host.move_card_to_hand_area(host.component_by_name(C_Q), 'host', (0, -100))  # just outside

        hand_area = host.hand_area(owner="host")
        host.drag(hand_area, 0, -100, 'top left')
        host.drag(hand_area, 0, -100, 'bottom')

        # host_card is no longer owned by host
        time.sleep(0.1)
        assert '♠A' in another.component_by_name(C_A).face()

        # PlayingCard S_3 is owned by host
        assert '♠Q' in host.component_by_name(C_Q).face()
        assert '♠Q' not in another.component_by_name(C_Q).face()

    def test_cards_on_hand_area_have_visible_clue(self, browser: webdriver.Firefox, another_browser: webdriver.Firefox):
        host = GameHelper(browser)
        another = GameHelper(another_browser)

        self.put_one_card_each_on_2_hand_areas(host, another)
        time.sleep(0.1)  # within detection is Level C user action, so it's safer to wait
        assert host.component_by_name(C_A).owner()
        assert host.component_by_name(C_K).owner()
        assert not host.component_by_name('PlayingCard H_A').owner()

    def test_removing_hand_area(self, browser: webdriver.Firefox, another_browser: webdriver.Firefox):
        host = GameHelper(browser)
        another = GameHelper(another_browser)
        self.put_one_card_each_on_2_hand_areas(host, another)

        host.menu.remove_my_hand_area.click()
        another.menu.remove_my_hand_area.click()

        assert not host.component_by_name(C_A).owner()
        assert not host.component_by_name(C_K).owner()
        assert not another.component_by_name(C_A).owner()
        assert not another.component_by_name(C_K).owner()

    def test_areas_boundary_is_correct(self, browser: webdriver.Firefox):
        host = GameHelper(browser)
        host.go(TOP)
        host.should_have_text("you are host")
        host.drag(host.component_by_name("usage"), 0, -200, 'lower right corner')
        host.menu.add_kit.execute()
        host.menu.add_kit_from_list("Playing Card")
        host.menu.add_kit_done()
        host.menu.add_my_hand_area.click()

        # move to inside of left top edge
        hand_area_rect = host.hand_area('host').rect()
        card_rect = host.component_by_name(C_A).rect()
        lt_in_offset = -(hand_area_rect.width - card_rect.width) / 2, -(hand_area_rect.height - card_rect.height) / 2
        host.move_card_to_hand_area(host.component_by_name(C_A), 'host', lt_in_offset)
        time.sleep(0.1)  # within detection is Level C user action, so it's safer to wait
        assert host.component_by_name(C_A).owner()

        # move to outside of left top edge
        lt_out_offset = lt_in_offset[0] - 1, lt_in_offset[1] - 1
        host.move_card_to_hand_area(host.component_by_name(C_A), 'host', lt_out_offset)
        time.sleep(0.1)  # within detection is Level C user action, so it's safer to wait
        assert not host.component_by_name(C_A).owner()

        # move to inside of right bottom edge
        rb_in_offset = (hand_area_rect.width - card_rect.width) / 2, (hand_area_rect.height - card_rect.height) / 2
        host.move_card_to_hand_area(host.component_by_name(C_A), 'host', rb_in_offset)
        time.sleep(0.1)  # within detection is Level C user action, so it's safer to wait
        assert host.component_by_name(C_A).owner()

        # move to outside of right bottom edge
        rb_out_offset = rb_in_offset[0] + 1, rb_in_offset[1] + 1
        host.move_card_to_hand_area(host.component_by_name(C_A), 'host', rb_out_offset)
        time.sleep(0.1)  # within detection is Level C user action, so it's safer to wait
        assert not host.component_by_name(C_A).owner()


@pytest.mark.usefixtures("server")
class TestDice:
    def test_add_dice_from_menu(self, browser: webdriver.Firefox):
        host = GameHelper(browser)
        host.go(TOP)
        host.should_have_text("you are host")

        host.menu.add_kit.execute()
        host.menu.add_kit_from_list("Dice (Blue)")

        assert host.component_by_name("Dice (Blue)")
        assert host.component_by_name("Dice (Blue)").rect().height == 64
        assert host.component_by_name("Dice (Blue)").rect().width == 64

    def test_show_number_of_dices_on_the_table(self, browser: webdriver.Firefox):
        host = GameHelper(browser)
        host.go(TOP)
        host.should_have_text("you are host")
        host.menu.add_kit.execute()

        host.menu.add_kit_from_list("Dice (Blue)")
        host.should_have_text("1 on the table")

        host.menu.add_kit_from_list("Dice (Blue)")
        host.should_have_text("2 on the table")

    @pytest.mark.skip
    def test_add_by_dragging(self, browser: webdriver.Firefox):
        pass

    @pytest.mark.skip
    def test_roll(self, browser: webdriver.Firefox):
        pass

    def test_remove_dice_from_table(self, browser: webdriver.Firefox):
        host = GameHelper(browser)
        host.go(TOP)
        host.menu.add_kit.execute()
        host.menu.add_kit_from_list("Dice (Blue)")

        host.menu.remove_kit_from_list("Dice (Blue)")
        host.should_not_see_component("Dice (Blue)")


@pytest.mark.usefixtures("server")
class TestCounter:
    @staticmethod
    def place_counter(host):
        host.go(TOP)
        host.should_have_text("you are host")

        host.menu.add_kit.execute()
        host.menu.add_kit_from_list("Counter")
        return host.component_by_name("Counter")

    def test_add_counter_from_menu(self, browser: webdriver.Firefox):
        host = GameHelper(browser)
        counter = self.place_counter(host)

        assert host.component_by_name("Counter")
        assert host.component_by_name("Counter").rect().height == 64
        assert host.component_by_name("Counter").rect().width == 96

    def test_initial_value(self, browser: webdriver.Firefox):
        host = GameHelper(browser)
        counter = self.place_counter(host)
        assert counter.element.find_element_by_css_selector(".counterValue").text == "0"

    class TestCounting:
        def test_add_1(self, browser: webdriver.Firefox):
            host = GameHelper(browser)
            counter = TestCounter.place_counter(host)
            counter.element.find_element_by_css_selector("button#addOne").click()
            assert counter.element.find_element_by_css_selector(".counterValue").text == "1"

        def test_sub_1(self, browser: webdriver.Firefox):
            host = GameHelper(browser)
            counter = TestCounter.place_counter(host)
            counter.element.find_element_by_css_selector("button#subOne").click()
            assert counter.element.find_element_by_css_selector(".counterValue").text == "-1"

        def test_add_10(self, browser: webdriver.Firefox):
            host = GameHelper(browser)
            counter = TestCounter.place_counter(host)
            counter.element.find_element_by_css_selector("button#addTen").click()
            assert counter.element.find_element_by_css_selector(".counterValue").text == "10"

        def test_sub_10(self, browser: webdriver.Firefox):
            host = GameHelper(browser)
            counter = TestCounter.place_counter(host)
            counter.element.find_element_by_css_selector("button#subTen").click()
            assert counter.element.find_element_by_css_selector(".counterValue").text == "-10"

        def test_reset(self, browser: webdriver.Firefox):
            host = GameHelper(browser)
            counter = TestCounter.place_counter(host)
            counter.element.find_element_by_css_selector("button#subOne").click()
            assert counter.element.find_element_by_css_selector(".counterValue").text == "-1"
            counter.element.find_element_by_css_selector("button#reset").click()
            assert counter.element.find_element_by_css_selector(".counterValue").text == "0"

        def test_succession_of_buttons(self, browser: webdriver.Firefox):
            host = GameHelper(browser)
            counter = TestCounter.place_counter(host)
            counter.element.find_element_by_css_selector("button#addOne").click()
            counter.element.find_element_by_css_selector("button#addOne").click()
            counter.element.find_element_by_css_selector("button#addTen").click()
            assert counter.element.find_element_by_css_selector(".counterValue").text == "12"

    class TestWithOtherPlayers:
        def test_add_1(self, browser: webdriver.Firefox, another_browser: webdriver.Firefox):
            host = GameHelper(browser)
            counter = TestCounter.place_counter(host)
            player = GameHelper(another_browser)
            player.go(host.current_url)
            player.menu.join("Player 2")
            player.should_have_text("you are Player 2")

            counter.element.find_element_by_css_selector("button#addOne").click()
            assert counter.element.find_element_by_css_selector(".counterValue").text == "1"
            assert player.component_by_name("Counter").element.find_element_by_css_selector(".counterValue").text == "1"

        def test_add_on_both(self, browser: webdriver.Firefox, another_browser: webdriver.Firefox):
            host = GameHelper(browser)
            counter = TestCounter.place_counter(host)
            player = GameHelper(another_browser)
            player.go(host.current_url)
            player.menu.join("Player 2")
            player.should_have_text("you are Player 2")

            counter.element.find_element_by_css_selector("button#addOne").click()
            player.component_by_name("Counter").element.find_element_by_css_selector("button#addTen").click()

            assert counter.element.find_element_by_css_selector(".counterValue").text == "11"
            assert player.component_by_name("Counter").element.find_element_by_css_selector(".counterValue").text == "11"

    class TestOverSession:
        def test_counter_is_retained_between_sessions(self, browser):
            host = GameHelper(browser)
            counter = TestCounter.place_counter(host)
            counter.element.find_element_by_css_selector("button#addOne").click()
            url = host.current_url

            host.go(url)
            assert host.component_by_name("Counter").element.find_element_by_css_selector(".counterValue").text == "1"


def test_unmovable_component_can_be_dragged_to_scroll(server, browser):
    host = GameHelper(browser)
    host.go(TOP)
    host.should_have_text("you are host")
    host.menu.add_kit.execute()
    host.menu.add_kit_from_list("Diamond Game")
    host.menu.add_kit_done()

    assert host.view_origin() == (0, 0)
    host.drag(host.component_by_name("Diamond Game Board"), 100, 100)
    assert host.view_origin() == (100, 100)


def test_moving_box_does_not_lose_things_within(server, browser: webdriver.Firefox):
    host = GameHelper(browser)
    host.go(TOP)
    host.should_have_text("you are host")
    host.drag(host.component_by_name("usage"), 0, -200, 'lower right corner')
    host.menu.add_kit.execute()
    host.menu.add_kit_from_list("Playing Card")
    host.menu.add_kit_done()

    for i in range(10):
        host.drag(host.component_by_name('Playing Card Box'), 10, 10, grab_at=(0, 80))

    box_rect = [c for c in host.all_components() if c.name == 'Playing Card Box'][0].rect()
    cards = [c for c in host.all_components()
             if c.name.startswith('PlayingCard ') or c.name.startswith('JOKER')]
    assert len(cards) == 54
    for card in cards:
        assert box_rect.left <= card.rect().left and card.rect().right <= box_rect.right
        assert box_rect.top <= card.rect().top and card.rect().bottom <= box_rect.bottom

