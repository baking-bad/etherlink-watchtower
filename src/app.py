import asyncio
import logging
from logging.config import dictConfig

from pydantic import Field
from pydantic_settings import BaseSettings
from pytezos import pytezos
from pytezos.rpc import RpcError
from python_graphql_client import GraphqlClient

from logs import LOGGING_CONFIG


class Settings(BaseSettings):
    graphql_endpoint: str = Field(alias='GRAPHQL_ENDPOINT')
    rpc_url: str = Field(alias='RPC_URL')
    private_key: str = Field(alias='PRIVATE_KEY')
    rollup_address: str = Field(alias='ROLLUP_ADDRESS')
    batch_size: int = Field(alias='BATCH_SIZE')


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def callback(response):
    batch = []
    logger.info('Sealed Withdrawals found. Preparing batch transaction.')
    if response['data']['bridge_operation_stream'] is None:
        return
    for item in response['data']['bridge_operation_stream']:
        outbox_message = item['withdrawal']['outbox_message']
        logger.info(
            'Processing `outbox_message` %d:%d...',
            outbox_message['level'],
            outbox_message['index'],
        )
        cemented_commitment = outbox_message['commitment']['hash']
        output_proof = outbox_message['proof']
        try:
            opg = client.smart_rollup_execute_outbox_message(
                rollup=config.rollup_address,
                cemented_commitment=cemented_commitment,
                output_proof=bytes.fromhex(output_proof),
            )
            opg.autofill()
            batch.append(opg)
        except RpcError as e:
            logger.error(
                'Outbox message %d:%d execution failed with %s: %s',
                outbox_message['level'],
                outbox_message['index'],
                e.__class__.__name__,
                e.args,
            )
    if batch:
        result = client.bulk(*batch).send(min_confirmations=1)
        logger.info(
            'Batch of %s transactions has been executed with hash `%s`.',
            len(batch),
            result.hash(),
        )


async def subscribe_to_sealed_withdrawals():
    query_variables = {'batch_size': config.batch_size}
    query = '''
    subscription SealedWithdrawals($batch_size: Int!) {
        bridge_operation_stream(
            batch_size: $batch_size,
            cursor: {initial_value: {updated_at: "2018-07-01"}, ordering: ASC},
            where: {
                type: {_eq: "withdrawal"},
                status: {_eq: "SEALED"},
                withdrawal: {outbox_message: {failure_count: {_is_null: true}}}
            }
        ) {
            withdrawal {
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
    '''
    await ws.subscribe(query=query, handle=callback, variables=query_variables)


if __name__ == '__main__':
    dictConfig(LOGGING_CONFIG)
    config = Settings()

    ws = GraphqlClient(endpoint=config.graphql_endpoint)

    client = pytezos.using(
        shell=config.rpc_url,
        key=config.private_key,
    )

    asyncio.run(subscribe_to_sealed_withdrawals())
