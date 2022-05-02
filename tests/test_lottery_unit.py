from brownie import exceptions
from scripts.helpful_scripts import get_account, get_contract, fund_with_link
from web3 import Web3
import pytest

# 0.016903599
# 16903599000000000
def test_get_entrance_fee(check_local_blockchain_envs, lottery_contract):
    # Arrange
    # Act
    # 2,790 eth / usd
    # usdEntryFee is 50
    # 2790/1 == 50/x == 0.017
    # expected_entrance_fee = Web3.toWei(0.017806983456376711, "ether")
    expected_entrance_fee = 17806983456376711
    entrance_fee = lottery_contract.getEntranceFee()
    # Assert
    assert entrance_fee == expected_entrance_fee


def test_cant_enter_unless_started(check_local_blockchain_envs, lottery_contract):
    # Arrange
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery_contract.enter({"from": get_account(), "value": lottery_contract.getEntranceFee()})
    

def test_can_start_and_enter_lottery(check_local_blockchain_envs, lottery_contract):
    # Arrange
    account = get_account()
    entrance_fee = lottery_contract.getEntranceFee()
    # Act
    lottery_contract.startLottery({"from": account})
    lottery_contract.enter({"from": account, "value": entrance_fee})
    # Assert
    assert lottery_contract.players(0) == account


def test_can_end_lottery(check_local_blockchain_envs, lottery_contract):
    # Arrange
    account = get_account()
    entrance_fee = lottery_contract.getEntranceFee()
    # Act
    lottery_contract.startLottery({"from": account})
    lottery_contract.enter({"from": account, "value": entrance_fee})
    fund_with_link(lottery_contract)
    lottery_contract.endLottery({"from": account})
    # Assert
    assert lottery_contract.lottery_state() == 2


def test_can_pick_winner_correctly(check_local_blockchain_envs, lottery_contract):
    # Arrange
    account = get_account()
    # Act
    lottery_contract.startLottery({"from": account})
    lottery_contract.enter({"from": account, "value": lottery_contract.getEntranceFee()})
    lottery_contract.enter({"from": get_account(index=1), "value": lottery_contract.getEntranceFee()})
    lottery_contract.enter({"from": get_account(index=2), "value": lottery_contract.getEntranceFee()})
    fund_with_link(lottery_contract)
    balance_of_lottery = lottery_contract.balance()
    starting_balance_of_account = account.balance()
    transaction = lottery_contract.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery_contract.address, {"from": account}
    )
    # Assert
    assert lottery_contract.recentWinner() == account
    assert lottery_contract.balance() == 0
    assert account.balance() == balance_of_lottery + starting_balance_of_account