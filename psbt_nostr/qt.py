#!/usr/bin/env python
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2014 Thomas Voegtlin
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import asyncio
import time
from typing import TYPE_CHECKING, Union, List, Tuple, Dict
import ssl
import json

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QPushButton

import electrum_ecc as ecc
import electrum_aionostr as aionostr

from electrum.crypto import sha256
from electrum import util
from electrum.transaction import Transaction, PartialTransaction, tx_from_any, SerializationError
from electrum.bip32 import BIP32Node
from electrum.plugin import BasePlugin, hook
from electrum.i18n import _
from electrum.wallet import Multisig_Wallet, Abstract_Wallet
from electrum.logging import Logger
from electrum.network import Network
from electrum.util import log_exceptions, OldTaskGroup

from electrum.gui.qt.transaction_dialog import show_transaction, TxDialog
from electrum.gui.qt.util import WaitingDialog

if TYPE_CHECKING:
    from electrum.gui.qt import ElectrumGui
    from electrum.gui.qt.main_window import ElectrumWindow


NOSTR_DM = 4

now = lambda: int(time.time())

class QReceiveSignalObject(QObject):
    cosigner_receive_signal = pyqtSignal(object, object)


class Plugin(BasePlugin):

    def __init__(self, parent, config, name):
        BasePlugin.__init__(self, parent, config, name)
        self._init_qt_received = False
        self.cosigner_wallets = {}  # type: Dict[Abstract_Wallet, CosignerWallet]


    @hook
    def init_qt(self, gui: 'ElectrumGui'):
        if self._init_qt_received:  # only need/want the first signal
            return
        self._init_qt_received = True
        for window in gui.windows:
            self.load_wallet(window.wallet, window)

    @hook
    def load_wallet(self, wallet: 'Abstract_Wallet', window: 'ElectrumWindow'):
        if type(wallet) != Multisig_Wallet:
            return
        self.cosigner_wallets[wallet] = CosignerWallet(wallet, window)

    @hook
    def on_close_window(self, window):
        wallet = window.wallet
        if cw := self.cosigner_wallets.get(wallet):
            cw.close()
            self.cosigner_wallets.pop(wallet)

    def is_available(self):
        return True

    @hook
    def transaction_dialog(self, d: 'TxDialog'):
        if cw := self.cosigner_wallets.get(d.wallet):
            cw.hook_transaction_dialog(d)

    @hook
    def transaction_dialog_update(self, d: 'TxDialog'):
        if cw := self.cosigner_wallets.get(d.wallet):
            cw.hook_transaction_dialog_update(d)


class CosignerWallet(Logger):
    # one for each open window
    # if user signs a tx, we have the password
    # if user receives a dm? needs to enter password first

    KEEP_DELAY = 24*60*60

    def __init__(self, wallet: 'Multisig_Wallet', window: 'ElectrumWindow'):
        assert isinstance(wallet, Multisig_Wallet)
        self.wallet = wallet
        self.network = window.network
        self.config = self.wallet.config
        self.window = window
        self.known_events = wallet.db.get_dict('cosigner_events')
        for k, v in list(self.known_events.items()):
            if v < now() - self.KEEP_DELAY:
                self.logger.info(f'deleting old event {k}')
                self.known_events.pop(k)

        self.relays = [self.config.get('nostr_relay', 'wss://relay.damus.io')]

        Logger.__init__(self)
        self.obj = QReceiveSignalObject()
        self.obj.cosigner_receive_signal.connect(self.on_receive)

        self.cosigner_list = []  # type: List[Tuple[str, bytes, str]]

        for key, keystore in wallet.keystores.items():
            xpub = keystore.get_master_public_key()  # type: str
            privkey = sha256('nostr_psbt:' + xpub)
            pubkey = ecc.ECPrivkey(privkey).get_public_key_bytes()[1:]
            if not keystore.is_watching_only():
                self.nostr_privkey = privkey.hex()
                self.nostr_pubkey = pubkey.hex()
            else:
                self.cosigner_list.append((xpub, pubkey.hex()))

        self.logger.info(f'nostr pubkey: {self.nostr_pubkey}')
        self.messages = asyncio.Queue()
        self.taskgroup = OldTaskGroup()
        asyncio.run_coroutine_threadsafe(self.main_loop(), self.network.asyncio_loop)

    @log_exceptions
    async def main_loop(self):
        self.logger.info("starting taskgroup.")
        try:
            async with self.taskgroup as group:
                await group.spawn(self.check_direct_messages())
        except Exception as e:
            self.logger.exception("taskgroup died.")
        finally:
            self.logger.info("taskgroup stopped.")

    async def stop(self):
        await self.taskgroup.cancel_remaining()

    @log_exceptions
    async def send_direct_messages(self, messages):
        for pubkey, msg in messages:
            await aionostr.add_event(
                self.relays,
                kind=NOSTR_DM,
                content=msg,
                direct_message=pubkey,
                private_key=self.nostr_privkey)
            self.logger.info(f'message sent to {pubkey}')

    async def check_direct_messages(self):
        queue = await aionostr.get_anything(
            {"kinds": [NOSTR_DM], "limit":1, "#p": [self.nostr_pubkey]},
            relays=self.relays,
            stream=True
        )
        while True:
            event = await queue.get()
            if event.id in self.known_events:
                continue
            if event.created_at > now() + self.KEEP_DELAY:
                # might be mallicious
                continue
            if event.created_at < now() - self.KEEP_DELAY:
                continue
            self.known_events[event.id] = now()
            privkey = aionostr.key.PrivateKey(bytes.fromhex(self.nostr_privkey))
            try:
                content = privkey.decrypt_message(event.content, event.pubkey)
            except:
                self.logger.info(f'could not decrypt message {event.pubkey}')
                continue
            self.logger.info(f"received message from {event.pubkey}")
            self.obj.cosigner_receive_signal.emit(event.pubkey, content)

    def diagnostic_name(self):
        return self.wallet.diagnostic_name()

    def close(self):
        self.logger.info("shutting down listener")
        asyncio.run_coroutine_threadsafe(self.stop(), self.network.asyncio_loop)

    def hook_transaction_dialog(self, d: 'TxDialog'):
        d.cosigner_send_button = b = QPushButton(_("Send to cosigner"))
        b.clicked.connect(lambda: self.do_send(d.tx))
        d.buttons.insert(0, b)
        b.setVisible(False)

    def hook_transaction_dialog_update(self, d: 'TxDialog'):
        assert self.wallet == d.wallet
        if d.tx.is_complete() or d.wallet.can_sign(d.tx):
            d.cosigner_send_button.setVisible(False)
            return
        for xpub, pubkey in self.cosigner_list:
            if self.cosigner_can_sign(d.tx, xpub):
                d.cosigner_send_button.setVisible(True)
                break
        else:
            d.cosigner_send_button.setVisible(False)

    def cosigner_can_sign(self, tx: Transaction, cosigner_xpub: str) -> bool:
        # TODO implement this properly:
        #      should return True iff cosigner (with given xpub) can sign and has not yet signed.
        #      note that tx could also be unrelated from wallet?... (not ismine inputs)
        return True

    def do_send(self, tx: Union[Transaction, PartialTransaction]):
        def on_result(result):
            self.window.show_message(
                _("Your transaction was sent to your cosigner via Nostr DM."))

        def on_failure(exc_info):
            e = exc_info[1]
            try: self.logger.error("on_failure", exc_info=exc_info)
            except OSError: pass
            self.window.show_error(_("Failed to send transaction to cosigning pool") + ':\n' + repr(e))

        buffer = []
        # construct messages
        for xpub, pubkey in self.cosigner_list:
            if not self.cosigner_can_sign(tx, xpub):
                continue
            raw_tx_bytes = tx.serialize_as_bytes()
            buffer.append((pubkey, raw_tx_bytes.hex()))
        if not buffer:
            return
        coro = self.send_direct_messages(buffer)
        text = _('Sending transaction to cosigning pool...')
        self.window.run_coroutine_dialog(coro, text, on_result, None)

    def on_receive(self, pubkey, message):
        #self.logger.info(f"signal arrived for {pubkey}")
        window = self.window
        wallet = self.wallet
        try:
            tx = tx_from_any(message)
        except SerializationError as e:
            self.logger.info(_("Unable to deserialize the transaction:") + "\n" + str(e))
            return

        if not window.question(
                _("An transaction was received from your cosigner.") + '\n' +
                _("Do you want to open it now?")):
            return
        show_transaction(tx, parent=window, prompt_if_unsaved=True)
