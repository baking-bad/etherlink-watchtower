import asyncio
import logging

from pydantic import Field
from pydantic_settings import BaseSettings
from pytezos import pytezos
from pytezos.rpc import RpcError
from python_graphql_client import GraphqlClient


class Settings(BaseSettings):
    graphql_endpoint: str = Field(alias='GRAPHQL_ENDPOINT')
    rpc_url: str = Field(alias='RPC_URL')
    private_key: str = Field(alias='PRIVATE_KEY')
    rollup_address: str = Field(alias='ROLLUP_ADDRESS')
    batch_size: int = Field(alias='BATCH_SIZE')


config = Settings()

ws = GraphqlClient(endpoint=config.graphql_endpoint)

client = pytezos.using(
    shell=config.rpc_url,
    key=config.private_key,
)

logger = logging.getLogger()


def callback(response):
    batch = []
    logger.info('Sealed Withdrawals found. Preparing batch transaction.')
    for item in response['data']['bridge_operation_stream']:
        cemented_commitment = item['withdrawal']['l2_transaction']['outbox_message']['commitment']['hash']
        output_proof = item['withdrawal']['l2_transaction']['outbox_message']['proof']
        try:
            opg = client.smart_rollup_execute_outbox_message(
                rollup=config.rollup_address,
                cemented_commitment=cemented_commitment,
                output_proof=bytes.fromhex(output_proof),
            )
            batch.append(opg)
        except RpcError as e:
            logger.error(str(e))
    result = client.bulk(*batch).send()
    logger.info(f'Batch of {len(batch)} transactions has been executed with hash `{result.hash()}`.')


async def subscribe_to_sealed_withdrawals():
    query_variables = {'batch_size': config.batch_size}
    query = '''
    subscription SealedWithdrawals($batch_size: Int!) {
        bridge_operation_stream(
            batch_size: $batch_size,
            cursor: {initial_value: {updated_at: "2018-07-01"}, ordering: ASC},
            where: {type: {_eq: "withdrawal"}, status: {_eq: "SEALED"}}
        ) {
            withdrawal {
                l2_transaction {
                    outbox_message {
                        index
                        level
                        proof
                        commitment {
                            hash
                            updated_at
                        }
                    }
                }
            }
        }
    }
    '''
    await ws.subscribe(query=query, handle=callback, variables=query_variables)


asyncio.run(subscribe_to_sealed_withdrawals())
